from pydantic import BaseModel


class UserInputWithSession(BaseModel):
    session_id: str = None
    message: str

