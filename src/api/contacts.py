from typing import List
from fastapi import APIRouter, Query, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database.db import get_db
from src.services.contacts import ContactsService
from src.schemas.contacts import (
    ContactBase,
    ContactUpdate,
    ContactResponse,
)

from src.schemas.users import UserBase
from src.services.auth import get_current_user

from src.exceptions.exceptions import (
    HTTPInternalDatabaseException,
    HTTPInternalUnexpectedException,
    HTTPNotFoundException,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    search: str | None = Query(
        default=None,
        description="Filter contacts by their first name, last name, or email.",
    ),
    birthdays_within_days: int | None = Query(
        default=None,
        description="Find contacts whose birthdays are within the given number of upcoming days.",
    ),
    skip: int | None = Query(
        default=None, description="Number of records to skip from the beginning."
    ),
    limit: int | None = Query(
        default=None, description="Maximum number of records to retrieve."
    ),
    db: AsyncSession = Depends(get_db),
    user: UserBase = Depends(get_current_user),
):
    try:
        contacts_service = ContactsService(db, user)
        return await contacts_service.get_all(
            search=search,
            birthdays_within_days=birthdays_within_days,
            skip=skip,
            limit=limit,
        )
    except SQLAlchemyError as e:
        raise HTTPInternalDatabaseException(str(e))
    except Exception as e:
        raise HTTPInternalUnexpectedException(str(e))


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
)
async def get_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserBase = Depends(get_current_user),
):
    try:
        contacts_service = ContactsService(db, user)
        contact = await contacts_service.get_by_id(contact_id)
        if contact is None:
            raise HTTPNotFoundException("Contact not found")
        return contact
    except SQLAlchemyError as e:
        raise HTTPInternalDatabaseException(str(e))
    except Exception as e:
        raise HTTPInternalUnexpectedException(str(e))


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ContactResponse,
)
async def create_contact(
    body: ContactBase,
    db: AsyncSession = Depends(get_db),
    user: UserBase = Depends(get_current_user),
):
    try:
        contacts_service = ContactsService(db, user)
        return await contacts_service.create(body)

    except SQLAlchemyError as e:
        raise HTTPInternalDatabaseException(str(e))
    except Exception as e:
        raise HTTPInternalUnexpectedException(str(e))


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
)
async def update_contact_by_id(
    body: ContactUpdate,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserBase = Depends(get_current_user),
):
    try:
        contacts_service = ContactsService(db, user)
        contact = await contacts_service.update_by_id(contact_id, body)
        if contact is None:
            raise HTTPNotFoundException("Contact not found")
        return contact
    except SQLAlchemyError as e:
        raise HTTPInternalDatabaseException(str(e))
    except Exception as e:
        raise HTTPInternalUnexpectedException(str(e))


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserBase = Depends(get_current_user),
):
    try:
        contacts_service = ContactsService(db, user)
        contact = await contacts_service.get_by_id(contact_id)
        if contact is None:
            raise HTTPNotFoundException("Contact not found")

        await contacts_service.delete_by_id(contact_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except SQLAlchemyError as e:
        raise HTTPInternalDatabaseException(str(e))
    except Exception as e:
        raise HTTPInternalUnexpectedException(str(e))
