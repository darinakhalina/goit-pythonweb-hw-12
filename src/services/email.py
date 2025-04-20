from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import SecretStr

from src.services.auth import create_token
from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: str, username: str, host: str):
    """
    Sends an email to the specified recipient for email verification.

    Args:
        email (str): The email address of the recipient.
        username (str): The username of the recipient.
        host (str): The host URL to include in the verification email template.
    """
    try:
        token_verification = create_token(payload={"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as e:
        print(e)


async def send_reset_email(email: str, token: str, host: str):
    """
    Sends a password reset email to the specified recipient.

    Args:
        email (str): The email address of the recipient.
        token (str): The password reset token.
        host (str): The host URL to include in the reset email template.
    """
    try:
        token = create_token(payload={"sub": email})
        message = MessageSchema(
            subject="Reset Password request",
            recipients=[email],
            template_body={
                "host": host,
                "token": token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password_email.html")
    except ConnectionErrors as e:
        print(e)
