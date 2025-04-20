import pytest
from unittest.mock import AsyncMock
from src.services.contacts import ContactsService
from src.schemas.contacts import ContactBase, ContactUpdate
from src.schemas.users import UserBase
from src.exceptions.exceptions import (
    HTTPNotFoundException,
    HTTPConflictRequestException,
)


@pytest.fixture
def user():
    return UserBase(
        id=1,
        username="testuser",
        email="test@example.com",
        role="user",
        avatar="some-test",
    )


@pytest.fixture
def mock_repo(monkeypatch):
    repo_mock = AsyncMock()
    monkeypatch.setattr(
        "src.services.contacts.ContactsRepository", lambda db, user: repo_mock
    )
    return repo_mock


@pytest.mark.asyncio
async def test_get_by_id_found(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = {"id": 1, "email": "a@a.com"}
    service = ContactsService(db=AsyncMock(), user=user)
    result = await service.get_by_id(1)
    assert result["id"] == 1
    mock_repo.get_contact_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = None
    service = ContactsService(db=AsyncMock(), user=user)

    with pytest.raises(HTTPNotFoundException):
        await service.get_by_id(99)


@pytest.mark.asyncio
async def test_create_conflict(mock_repo, user):
    mock_repo.get_contact_by_email.return_value = {
        "id": 1,
        "email": "exist@example.com",
    }
    service = ContactsService(db=AsyncMock(), user=user)

    with pytest.raises(HTTPConflictRequestException):
        await service.create(
            ContactBase(
                email="exist@example.com",
                first_name="Test",
                last_name="User",
                phone="123",
                birthday="2000-01-01",
            )
        )


@pytest.mark.asyncio
async def test_update_by_id_success(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = {"id": 1, "email": "a@a.com"}
    mock_repo.update.return_value = {"id": 1, "email": "updated@example.com"}

    service = ContactsService(db=AsyncMock(), user=user)
    update_data = ContactUpdate(
        email="updated@example.com",
        first_name="Updated",
        last_name="User",
        phone="999",
        birthday="2000-01-01",
    )
    result = await service.update_by_id(1, update_data)

    assert result["email"] == "updated@example.com"
    mock_repo.update.assert_awaited_once_with(1, update_data)


@pytest.mark.asyncio
async def test_update_by_id_not_found(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = None
    service = ContactsService(db=AsyncMock(), user=user)

    with pytest.raises(HTTPNotFoundException):
        await service.update_by_id(
            99,
            ContactUpdate(
                email="noone@example.com",
                first_name="Nobody",
                last_name="Here",
                phone="000",
                birthday="1990-01-01",
            ),
        )


@pytest.mark.asyncio
async def test_delete_by_id_success(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = {"id": 1, "email": "a@a.com"}
    mock_repo.delete.return_value = {"message": "deleted"}
    service = ContactsService(db=AsyncMock(), user=user)
    result = await service.delete_by_id(1)

    assert result["message"] == "deleted"
    mock_repo.delete.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_delete_by_id_not_found(mock_repo, user):
    mock_repo.get_contact_by_id.return_value = None
    service = ContactsService(db=AsyncMock(), user=user)

    with pytest.raises(HTTPNotFoundException):
        await service.delete_by_id(404)


@pytest.mark.asyncio
async def test_get_all_contacts(mock_repo, user):
    mock_repo.get_all.return_value = [
        {"id": 1, "email": "first@example.com"},
        {"id": 2, "email": "second@example.com"},
    ]
    service = ContactsService(db=AsyncMock(), user=user)
    result = await service.get_all(
        search=None, birthdays_within_days=None, skip=0, limit=10
    )

    assert len(result) == 2
    assert result[0]["email"] == "first@example.com"
    mock_repo.get_all.assert_awaited_once_with(
        search=None, birthdays_within_days=None, skip=0, limit=10
    )


@pytest.mark.asyncio
async def test_create_success(mock_repo, user):
    mock_repo.get_contact_by_email.return_value = None
    mock_repo.create.return_value = {"id": 2, "email": "new@example.com"}
    service = ContactsService(db=AsyncMock(), user=user)
    contact = ContactBase(
        email="new@example.com",
        first_name="New",
        last_name="User",
        phone="456",
        birthday="1995-05-05",
    )
    result = await service.create(contact)

    assert result["email"] == "new@example.com"
    mock_repo.create.assert_awaited_once_with(contact)
