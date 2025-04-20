from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactBase, ContactUpdate
from src.schemas.users import UserBase
from src.exceptions.exceptions import (
    HTTPNotFoundException,
    HTTPConflictRequestException,
)


class ContactsService:
    repository: ContactsRepository
    current_user: UserBase

    def __init__(self, db: AsyncSession, user: UserBase):
        self.repository = ContactsRepository(db, user)
        self.current_user = user

    async def get_all(
        self,
        search: str | None = None,
        birthdays_within_days: int | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ):
        """
        Retrieves all contacts for the current user, with optional filtering and pagination.

        Args:
            search (str | None): Optional search term to filter by first name, last name, or email.
            birthdays_within_days (int | None): If specified, filters contacts with birthdays within the next N days.
            skip (int | None): Number of records to skip for pagination.
            limit (int | None): Maximum number of records to return.

        Returns:
            List[Contact]: A list of contact objects matching the criteria.
        """
        return await self.repository.get_all(
            search=search,
            birthdays_within_days=birthdays_within_days,
            skip=skip,
            limit=limit,
        )

    async def get_by_id(self, contact_id: int):
        """
        Retrieves a contact by its ID for the current user.

        Args:
            contact_id (int): The ID of the contact to retrieve.

        Returns:
            Contact: The contact object if found.
        """
        contact = await self.repository.get_contact_by_id(contact_id)

        if contact is None:
            raise HTTPNotFoundException("Not found")

        return contact

    async def create(self, body: ContactBase):
        """
        Creates a new contact for the current user.

        Args:
            body (ContactBase): The contact data to create.

        Returns:
            Contact: The newly created contact.
        """
        contact = await self.repository.get_contact_by_email(body.email)

        if contact:
            raise HTTPConflictRequestException(
                "Cannot create contact, email already registered."
            )

        return await self.repository.create(body)

    async def update_by_id(self, contact_id: int, body: ContactUpdate):
        """
        Updates an existing contact by ID for the current user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactUpdate): The fields to update in the contact.

        Returns:
            Contact: The updated contact.
        """
        contact = await self.repository.get_contact_by_id(contact_id)

        if not contact:
            raise HTTPNotFoundException("Not found")

        return await self.repository.update(contact_id, body)

    async def delete_by_id(self, contact_id: int):
        """
        Deletes an existing contact by ID for the current user.

        Args:
            contact_id (int): The ID of the contact to delete.

        Returns:
            Contact: The deleted contact.
        """
        contact = await self.repository.get_contact_by_id(contact_id)

        if contact is None:
            raise HTTPNotFoundException("Not found")

        return await self.repository.delete(contact_id)
