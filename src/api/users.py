from fastapi import APIRouter, Depends, File, UploadFile, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db

from src.schemas.users import UserBase
from src.services.auth import get_current_user, get_current_user_admin
from src.services.cache import update_cached_current_user
from src.services.users import UserService
from src.services.upload import UploadService, CloudinaryUploadService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me", response_model=UserBase, description="Limited to 10 requests per minute."
)
@limiter.limit("10/minute")
async def me(request: Request, user: UserBase = Depends(get_current_user)):
    """
    Get the details of the currently authenticated User.

    Args:
        request (Request): The request object, used to access request-related data.
        user (UserBase): The currently authenticated user, provided via dependency injection.

    Returns:
        UserBase: The details of the authenticated User.
    """
    return user


@router.patch("/avatar", response_model=UserBase)
async def update_avatar_user(
    file: UploadFile = File(),
    user: UserBase = Depends(get_current_user_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the avatar of the currently authenticated user.

    Args:
        file (UploadFile): The avatar image file to be uploaded.
        user (UserBase): The currently authenticated admin user, provided via dependency injection.
        db (AsyncSession): The database session used to update user information.

    Returns:
        UserBase: The updated user with the new avatar URL.
    """
    upload_service = UploadService(CloudinaryUploadService())
    avatar_url = upload_service.upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)
    await update_cached_current_user(user)

    return user
