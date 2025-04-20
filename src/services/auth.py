from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import logging

from src.database.db import get_db
from src.database.models import UserRole, User
from src.services.cache import get_cached_current_user, update_cached_current_user
from src.conf.config import settings
from src.services.users import UserService
from src.exceptions.exceptions import (
    HTTPUnauthorizedException,
    HTTPBadRequestException,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(payload: dict, expires_delta: Optional[int] = None):
    """
    Create a JWT access token.

    Args:
        payload (dict): The payload to include in the JWT, typically containing user identification data (e.g., email, user ID).
        expires_delta (Optional[int]): The expiration time in seconds for the token. If not provided, the default expiration
        time from settings will be used.

    Returns:
        str: The encoded JWT access token.
    """
    payload_data = payload.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            seconds=int(settings.JWT_EXPIRATION_SECONDS)
        )
    payload_data.update({"exp": expire})
    encoded = jwt.encode(
        payload_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded


def create_token(payload: dict):
    """
    Create a JWT token with a 7-day expiration.

    Args:
        payload (dict): A dictionary containing the data to encode in the JWT.
        This typically includes identifying information such as user ID or email.

    Returns:
        str: A JWT token as a string.
    """
    to_encode = payload.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the currently authenticated user from the JWT token.

    Args:
        token (str): A JWT token automatically extracted from the Authorization header by FastAPI's `oauth2_scheme`.
        db (AsyncSession): SQLAlchemy asynchronous database session (injected via dependency).

    Returns:
        User: The user object corresponding to the username in the token payload.
    """
    credentials_exception = HTTPUnauthorizedException("Could not validate credentials")

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cached_user = await get_cached_current_user(username)
    if cached_user:
        logger.info(f'Get user data from cache - "{cached_user.username}".')
        return cached_user

    logger.info(f'Search for user data "{username}" in db.')
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    await update_cached_current_user(user)
    return user


def get_current_user_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency that ensures the current user has admin privileges.

    Args:
        current_user (User): The currently authenticated user, injected via `get_current_user`.

    Returns:
        User: The same user object if they have admin rights.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission Denided")
    return current_user


async def get_email_from_token(token: str):
    """
    Decodes a JWT token and extracts the email from its payload.

    Args:
        token (str): The JWT token to decode.

    Returns:
        str: The email extracted from the token's "sub" claim.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError:
        raise HTTPBadRequestException("Invalid or expired token")
