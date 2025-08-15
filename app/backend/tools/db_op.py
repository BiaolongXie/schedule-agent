import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor

import pymysql
from pymysql.cursors import Cursor

from app.common.db_config import Config


DB_CONFIG = {
    'host': Config.MYSQL_HOST,
    'port': Config.MYSQL_PORT,
    'user': Config.MYSQL_USER,
    'password': Config.MYSQL_PASSWORD,
    'db': Config.DATABASE_NAME,
    'autocommit': False
}

# 创建一个全局的线程池执行器
# 最佳的 `max_workers` 数量取决于您的应用负载和服务器核心数
executor = ThreadPoolExecutor(max_workers=10)


# --- 数据库连接上下文管理器 (无需修改) ---
class DatabaseConnection:
    def __init__(self, config):
        self._config = config
        self._connection = None
        self._cursor = None

    def __enter__(self) -> Cursor:
        try:
            self._connection = pymysql.connect(**self._config)
            self._cursor = self._connection.cursor()
            return self._cursor
        except pymysql.MySQLError as e:
            print(f"数据库连接失败: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            try:
                if exc_type:
                    self._connection.rollback()
                    print(f"事务已回滚，因为发生了错误: {exc_val}")
                else:
                    self._connection.commit()
            finally:
                if self._cursor:
                    self._cursor.close()
                self._connection.close()
        # 返回 False 以便在 __exit__ 之外重新引发异常
        return False


def get_today_date():
    """用于给llm获取当天日期"""
    return datetime.date.today()

def _sync_get_all_schedules_by_userid(userid: int):
    """同步实现：通过userid查询用户所有的计划"""
    sql = "SELECT * FROM schedules WHERE user_id = %s;"
    value = (userid)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, value)
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"查询日程数据库时出错: {e}")
        return ()

async def get_all_schedules_by_userid(userid: int):
    """异步接口：通过userid查询用户所有的计划"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_get_all_schedules_by_userid, userid
    )

def _sync_get_schedules_by_data(userid: int, date: str):
    """同步实现：通过userid和日期查询用户所有的计划"""
    sql = "SELECT * FROM schedules WHERE user_id = %s and date = %s;"
    value = (userid, date)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, value)
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"查询日程数据库时出错: {e}")
        return ()

async def get_schedules_by_data(userid: int, date: str):
    """异步接口：通过userid和日期查询用户所有的计划"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_get_schedules_by_data, userid, date
    )

def _sync_add_schedule(userid: int, date: str, title: str, time=None, description: str = None) -> bool:
    """同步实现：向数据库中插入一条新的计划"""
    sql = "INSERT INTO schedules (user_id, date, title, time, description) VALUES (%s, %s, %s, %s, %s);"
    values = (userid, date, title, time, description)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, values)
        print(f"成功为用户 {userid} 插入日程数据。")
        return True
    except pymysql.MySQLError as e:
        print(f"为用户 {userid} 插入数据失败: {e}")
        return False

async def add_schedule(userid: int, date: str, title: str, time=None, description: str = None) -> bool:
    """异步接口：向数据库中插入一条新的计划"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_add_schedule, userid, date, title, time, description
    )

def _sync_remove_schedule_by_date(userid: int, date: str) -> bool:
    """同步实现：根据用户id和指定日期删除日程"""
    sql = "DELETE FROM schedules WHERE user_id = %s AND date = %s;"
    values = (userid, date)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, values)
        print(f"成功删除用户 {userid} 在 {date} 的日程数据。")
        return True
    except pymysql.MySQLError as e:
        print(f"删除失败: {e}")
        return False

async def remove_schedule_by_date(userid: int, date: str) -> bool:
    """异步接口：根据用户id和指定日期删除日程"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_remove_schedule_by_date, userid, date
    )

def _sync_remove_schedule_by_userid(userid: int) -> bool:
    """同步实现：根据用户id删除用户所有日程"""
    sql = "DELETE FROM schedules WHERE user_id = %s;"
    values = (userid,)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, values)
        print(f"成功删除用户 {userid} 的所有日程数据。")
        return True
    except pymysql.MySQLError as e:
        print(f"删除失败: {e}")
        return False

async def remove_schedule_by_userid(userid: int) -> bool:
    """异步接口：根据用户id删除用户所有日程"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_remove_schedule_by_userid, userid
    )

def _sync_remove_schedule_by_id(schedule_id: int, userid: int) -> bool:
    """同步实现：根据日程id和用户id删除指定日程"""
    sql = "SELECT id FROM schedules WHERE user_id = %s;"
    value = (userid)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, value)
            schedule_ids = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"查询日程数据库时出错: {e}")
        return False

    if (schedule_id,) not in schedule_ids:
        return False
    else:
        sql = "DELETE FROM schedules WHERE user_id = %s and id = %s;"
        values = (userid, schedule_id)
        try:
            with DatabaseConnection(DB_CONFIG) as cursor:
                cursor.execute(sql, values)
            print(f"成功删除日程ID {schedule_id} (用户 {userid}) 的数据。")
            return True
        except pymysql.MySQLError as e:
            print(f"删除失败: {e}")
            return False

async def remove_schedule_by_id(schedule_id: int, userid: int) -> bool:
    """异步接口：根据日程id和用户id删除指定日程"""
    loop = asyncio.get_running_loop()
    # 注意参数顺序要与同步函数一致
    return await loop.run_in_executor(
        executor, _sync_remove_schedule_by_id, schedule_id, userid
    )

def _sync_get_user_from_db(userid):
    """同步实现：通过userid查询用户所有信息"""
    sql = "SELECT * FROM users WHERE id = %s;"
    value = (userid)
    try:
        with DatabaseConnection(DB_CONFIG) as cursor:
            cursor.execute(sql, value)
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"查询日程数据库时出错: {e}")
        return ()

async def get_user_from_db(userid):
    """异步接口：通过userid查询用户所有信息"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, _sync_get_user_from_db, userid
    )




# if __name__ == "__main__":
#     print(asyncio.run(get_all_schedules_by_userid(1)))
    # print(asyncio.run(remove_schedule_by_id(9, 2)))
    # print(asyncio.run(get_user_from_db(1)))
