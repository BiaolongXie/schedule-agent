from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat_router

app = FastAPI()

# 添加 CORS 中间件，允许来自您前端的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(chat_router.router)

# 启动指令：gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:8000
# uvicorn app.main:app --reload --port 8080