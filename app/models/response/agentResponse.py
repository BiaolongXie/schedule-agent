from pydantic import BaseModel


class AgentResponse(BaseModel):
    session_id: str
    message: str
