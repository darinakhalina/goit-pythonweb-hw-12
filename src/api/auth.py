from fastapi import APIRouter, Depends, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.cache import update_cached_current_user
from fastapi.security import OAuth2PasswordRequestForm
import logging


from src.schemas.users import (
    UserBase,
    UserCreate,
    ResetPasswordRequest,
    ResetPasswordConfirm,
    UserUpdate,
)
from src.schemas.token import Token
from src.services.auth import (
    create_access_token,
    Hash,
    get_email_from_token,
    create_token,
)
from src.services.users import UserService
from src.services.email import send_email, send_reset_email
from src.database.db import get_db
from src.exceptions.exceptions import (
    HTTPConflictRequestException,
    HTTPUnauthorizedException,
    HTTPBadRequestException,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new User and send a confirmation email.

    Args:
        user (UserCreate): The user data for registration, including username, email, and password.
        background_tasks (BackgroundTasks): Used to send the confirmation email asynchronously.
        request (Request): The request object used to extract the base URL.
        db (AsyncSession): The database session used to interact with the database.

    Returns:
        UserBase: The created User with their details, including the username and email.
    """
    user_service = UserService(db)
    email_user = await user_service.get_user_by_email(user.email)

    if email_user:
        raise HTTPConflictRequestException("Cannot create user, email already in use.")

    username_user = await user_service.get_user_by_username(user.username)

    if username_user:
        raise HTTPConflictRequestException(
            "Cannot create user, username already exists."
        )

    user.password = Hash().get_password_hash(user.password)
    new_user = await user_service.create_user(user)

    background_tasks.add_task(
        send_email, str(new_user.email), str(new_user.username), str(request.base_url)
    )

    logger.info(f'Email sent for "{new_user.username}".')

    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    request_form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a User and return a JWT token.

    Args:
        request_form (OAuth2PasswordRequestForm): The login form containing username and password.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(request_form.username)

    if not user:
        raise HTTPUnauthorizedException("Incorrect login or/and password.")

    if not user.confirmed:
        raise HTTPUnauthorizedException("User is not confirmed.")

    password_verified = Hash().verify_password(request_form.password, user.password)

    if not password_verified:
        raise HTTPUnauthorizedException("Incorrect login or/and password.")

    await update_cached_current_user(user)
    payload = {"sub": user.username}
    access_token = await create_access_token(payload)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify_email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify the User's email using a token.

    Args:
        token (str): The verification token sent to the user's email.
        db (AsyncSession): The database session used to interact with the database.

    Returns:
        dict: A message indicating the result of the verification process:
            - "Email is already confirmed." if the email was previously verified.
            - "Email has been successfully confirmed." upon successful verification.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPBadRequestException("Verification error")

    if bool(user.confirmed):
        return {"message": "Email is already confirmed."}

    await user_service.verify_email(email)
    logger.info(f"Email address {email} verified.")
    await update_cached_current_user(user)
    return {"message": "Email has been successfully confirmed."}


@router.post("/password-reset/")
async def password_reset(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate a password reset process by sending a reset link to the User's email.

    Args:
        body (ResetPasswordRequest): The request body containing the email of the user requesting the password reset.
        background_tasks (BackgroundTasks): Used to send the reset email in the background.
        request (Request): The request object to get the base URL for the reset link.
        db (AsyncSession): The database session used to interact with the database.

    Returns:
        dict: A message indicating that the password reset email has been sent.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if not user:
        raise HTTPUnauthorizedException()

    token = create_token(payload={"sub": body.email})

    background_tasks.add_task(
        send_reset_email,
        body.email,
        token,
        str(request.base_url),
    )

    logger.info(
        f'Reset password email sent for a user with email address "{body.email}".'
    )
    await update_cached_current_user(user)
    return {"message": "Reset password email sent"}


@router.post("/password-reset-confirm/")
async def password_reset_confirm(
    data: ResetPasswordConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm the password reset by validating the token and updating the User's password.

    Args:
        data (ResetPasswordConfirm): The request body containing the token and the new password.
        db (AsyncSession): The database session used to interact with the database.

    Returns:
        dict: A message indicating that the password has been successfully updated.
    """
    user_service = UserService(db)
    email = await get_email_from_token(data.token)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPBadRequestException("Invalid or expired token")

    new_password = Hash().get_password_hash(data.password)
    password_added = await user_service.update_user(
        user, UserUpdate(password=new_password)
    )

    if password_added:
        logger.info(f'Password updated for a user with email "{email}".')
        return {"message": "Password updated"}
