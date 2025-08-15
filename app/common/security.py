import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError

from app.backend.tools.db_op import get_user_from_db
from app.common.db_config import Config

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_user_token(token: str = Depends(oauth2_scheme)):
    return token



async def get_user_id_from_token(token) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[ALGORITHM])
        userid: str = payload.get("sub")
        if userid is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    result = get_user_from_db(userid)
    if result is None:
        raise credentials_exception

    return userid