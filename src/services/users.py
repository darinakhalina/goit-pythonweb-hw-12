from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate
from src.exceptions.exceptions import (
    HTTPNotFoundException,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Creates a new user, generating an avatar from the user's email if possible.

        Args:
            body (UserCreate): Pydantic model containing the data for creating the user.

        Returns:
            User: The created `User` object with all the details.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Fetches a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The user object corresponding to the provided ID.
        """
        user = await self.repository.get_user_by_id(user_id)

        if not user:
            raise HTTPNotFoundException("Not found")

        return user

    async def get_user_by_username(self, username: str):
        """
        Fetches a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user object corresponding to the provided username,
            or None if no user with that username is found.
        """
        user = await self.repository.get_user_by_username(username)
        return user

    async def get_user_by_email(self, email: str):
        """
        Fetches a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user object corresponding to the provided email address,
                         or None if no user with that email is found.
        """
        user = await self.repository.get_user_by_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        """
        Updates the avatar URL for a user identified by their email address.

        Args:
            email (str): The email address of the user whose avatar is to be updated.
            url (str): The new avatar URL to assign to the user.

        Returns:
            User: The updated user object with the new avatar URL.
        """
        user = await self.get_user_by_email(email)

        if not user:
            raise HTTPNotFoundException("Not found")

        return await self.repository.update_avatar_url(email, url)

    async def verify_email(self, email: str):
        """
        Verifies a user's email by setting their 'confirmed' status to True.

        Args:
            email (str): The email address of the user to be verified.

        Returns:
            None
        """
        await self.repository.verify_email(email)

    async def update_user(self, user: User, body: UserUpdate):
        """
        Updates a user's information with the provided data.

        Args:
            user (User): The existing user to be updated.
            body (UserUpdate): The data to update the user with.

        Returns:
            bool: Returns `True` if the user was successfully updated.
        """
        return await self.repository.update_user(user, body)
