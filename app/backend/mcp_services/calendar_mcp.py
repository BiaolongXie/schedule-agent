from mcp.server.fastmcp import FastMCP

from app.common.security import get_user_id_from_token
from ..tools.db_op import *

mcp = FastMCP("ScheduleServer")

@mcp.tool()
def get_today():
    """
    调用此工具获取今日日期

    :return: 今日日期
    """
    return get_today_date()

@mcp.tool()
async def mcp_get_all_schedules_by_userid(token: str):
    """
    Retrieve all schedule plans of the user through their ID

    :param token: 一个用于存储用户登录信息的token
    :return: a list containing schedule plan
    """
    userid = int(await get_user_id_from_token(token))
    schedules = await get_all_schedules_by_userid(userid)
    list = []
    for schedule in schedules:
        data = {}
        data["schedule_id"] = schedule[0]
        data["user_id"] = schedule[1]
        data["title"] = schedule[2]
        data["description"] = schedule[3]
        data["date"] = schedule[4]
        data["time"] = schedule[5]
        list.append(data)
    return list

@mcp.tool()
async def mcp_get_schedules_by_data(token: str, date: str):
    """
    Retrieve the schedule for the user specified date through the user ID and date,
    The return time is a time point within a day, not a period of several hours

    :param token: 一个用于存储用户登录信息的token
    :param date: string
    :return: a list containing schedule plan
    """
    userid = int(await get_user_id_from_token(token))
    schedules = await get_schedules_by_data(userid, date)
    list = []
    for schedule in schedules:
        data = {}
        data["schedule_id"] = schedule[0]
        data["user_id"] = schedule[1]
        data["title"] = schedule[2]
        data["description"] = schedule[3]
        data["date"] = schedule[4]
        data["time"] = schedule[5]
        list.append(data)
    return list

@mcp.tool()
async def mcp_add_schedule(token: str, date: str, title: str, time=None, description: str = None):
    """
    Add the schedule to the database based on the information provided by the user,among them, userid, date, and title are required parameters. If not all three are met, this tool is not allowed to be called. Continue to ask the user for supplementary information to know if the conditions are met

    :param token: 一个用于存储用户登录信息的token (must)
    :param date: string (must)
    :param title: string (must)
    :param time: string (optional) Using 24-hour timing method，The format is hh: mm: ss. For example:08:30:00 indicate 8:30 am
    :param description: string (optional)
    :return: 日程添加是否成功
    """
    userid = int(await get_user_id_from_token(token))
    result = await add_schedule(userid, date, title, time, description)
    if result:
        return "日程添加成功"
    else:
        return "日程添加失败"

@mcp.tool()
async def mcp_remove_schedule_by_date(token: str, date: str):
    """
    Delete all plans for user specified dates

    :param token: 一个用于存储用户登录信息的token (must)
    :param date: string (must)
    :return: whether remove success
    """
    userid = int(await get_user_id_from_token(token))
    result = await remove_schedule_by_date(userid, date)
    if result:
        return "Successfully deleted"
    else:
        return "Unsuccessful deleted"

@mcp.tool()
async def mcp_remove_schedule_by_userid(token: str):
    """
    Delete all user plans by userid

    :param token: 一个用于存储用户登录信息的token (must)
    :return: whether remove success
    """
    userid = int(await get_user_id_from_token(token))
    result = await remove_schedule_by_userid(userid)
    if result:
        return "Successfully deleted"
    else:
        return "Unsuccessful deleted"

@mcp.tool()
async def mcp_remove_schedule_by_schedule_id(id: int, token: str):
    """
    The user must delete the schedule with the specified schedule_id, and the schedule must belong to this user. If not, please prohibit the user from performing this operation and confirm the information with the user

    :param id: integer (must) schedule_id
    :param token: 一个用于存储用户登录信息的token (must)
    :return: whether remove success
    """
    userid = int(await get_user_id_from_token(token))
    result = await remove_schedule_by_id(id, userid)

    if result:
        return "Successfully deleted"
    else:
        return "The user does not have a relevant plan ID"


if __name__ == "__main__":
    mcp.run(transport="stdio")
