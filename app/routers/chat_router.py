import uuid

from fastapi import APIRouter, HTTPException
from fastapi import Depends

from app.backend.client import agent
from app.common.security import get_user_token
from app.models.request.userInputWithSession import UserInputWithSession
from app.models.response.agentResponse import AgentResponse

router = APIRouter(
    prefix="/api/agent/schedule_agent",
    tags=["agent"]
)


@router.post("/chat/v1", response_model=UserInputWithSession)
async def chat_with_agent(request: UserInputWithSession, user_token: str = Depends(get_user_token)):
    """
    与日历 agent 对话的端点。
    """
    try:
        # 如果请求中没有 session_id，则创建一个新的
        session_id = request.session_id or str(uuid.uuid4())

        answer = await agent.chat_with_agent(request.message, request.session_id, user_token)

        return AgentResponse(message=answer, session_id=session_id)
    except Exception as e:
        # 捕获异常并返回详细的错误信息
        raise HTTPException(status_code=500, detail=str(e))



