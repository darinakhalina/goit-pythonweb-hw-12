from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from src.exceptions.exceptions import HTTPNotFoundException


def test_get_contacts_authenticated(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    contact_data = {
        "user_id": 1,
        "first_name": "Deadpool",
        "last_name": "Wade",
        "email": "deadpool@example.com",
        "phone": "1234567890",
        "birthday": "1980-10-12",
    }

    create_contact_response = client.post(
        "/api/contacts/", json=contact_data, headers=headers
    )
    assert create_contact_response.status_code == 201, create_contact_response.text
    response = client.get("/api/contacts/", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()

    assert len(data) > 0, "Expected contacts to be returned"

    assert "first_name" in data[0], "First name field is missing"
    assert "last_name" in data[0], "Last name field is missing"
    assert "email" in data[0], "Email field is missing"


def test_get_contacts_with_search(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    contacts = [
        {
            "first_name": "Wade",
            "last_name": "Wilson",
            "email": "wade@example.com",
            "phone": "123456789",
            "birthday": "1980-05-10",
        },
        {
            "first_name": "Logan",
            "last_name": "Howlett",
            "email": "logan@example.com",
            "phone": "987654321",
            "birthday": "1975-11-20",
        },
    ]

    for contact in contacts:
        response = client.post("/api/contacts/", json=contact, headers=headers)
        assert response.status_code == 201, response.text

    response = client.get(
        "/api/contacts/", headers=headers, params={"search": "Wilson"}
    )
    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1, f"Expected 1 contact, got {len(data)}"
    assert data[0]["first_name"] == "Wade"
    assert data[0]["last_name"] == "Wilson"
    assert data[0]["email"] == "wade@example.com"


def test_get_contact_sqlalchemy_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = SQLAlchemyError("Database error occurred.")

    with patch("src.api.contacts.ContactsService.get_all", side_effect=error_instance):
        response = client.get("api/contacts/", headers=headers)

    assert response.status_code == 500
    assert response.json() == {"detail": "Database error occurred."}


def test_get_contact_unexpected_exception(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = Exception("Unexpected error occurred.")

    with patch("src.api.contacts.ContactsService.get_all", side_effect=error_instance):
        response = client.get("api/contacts/", headers=headers)

    assert response.status_code == 500
    assert response.json() == {"detail": "Unexpected error occurred."}


def test_get_contacts_success(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    contact_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone": "1234567890",
        "birthday": "1990-01-01",
    }

    create_response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert create_response.status_code == 201, create_response.text
    contact_id = create_response.json()["id"]

    response = client.get(f"api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["first_name"] == "Test"


def test_get_contact_by_id_sqlalchemy_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = SQLAlchemyError("DB failure")

    with patch(
        "src.api.contacts.ContactsService.get_by_id", side_effect=error_instance
    ):
        response = client.get("api/contacts/1", headers=headers)

    assert response.status_code == 500
    assert response.json() == {"detail": "DB failure"}


def test_get_contact_by_id_unexpected_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = Exception("An unexpected error occurred.")

    with patch(
        "src.api.contacts.ContactsService.get_by_id", side_effect=error_instance
    ):
        response = client.get("api/contacts/1", headers=headers)

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}


def test_get_contact_by_id_not_found(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    with patch("src.api.contacts.ContactsService.get_by_id", return_value=None):
        response = client.get("/api/contacts/1", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Contact not found"}


def test_get_contact_by_id_success(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    mock_contact = {
        "id": 1,
        "user_id": 1,
        "first_name": "Bruce",
        "last_name": "Wayne",
        "email": "bruce@wayne.com",
        "phone": "1234567890",
        "birthday": "1985-02-19",
    }

    with patch("src.api.contacts.ContactsService.get_by_id", return_value=mock_contact):
        response = client.get("/api/contacts/1", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == mock_contact["id"]
    assert data["first_name"] == mock_contact["first_name"]
    assert data["last_name"] == mock_contact["last_name"]
    assert data["email"] == mock_contact["email"]


def test_create_contact_sqlalchemy_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = SQLAlchemyError("Database error occurred.")

    with patch("src.api.contacts.ContactsService.create", side_effect=error_instance):
        response = client.post(
            "/api/contacts/",
            json={
                "first_name": "Bruce",
                "last_name": "Wayne",
                "email": "bruce@wayne.com",
                "phone": "1234567890",
                "birthday": "1985-02-19",
            },
            headers=headers,
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Database error occurred."}


def test_create_contact_unexpected_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    error_instance = Exception("Unexpected error occurred.")

    with patch("src.api.contacts.ContactsService.create", side_effect=error_instance):
        response = client.post(
            "/api/contacts/",
            json={
                "first_name": "Clark",
                "last_name": "Kent",
                "email": "clark@dailyplanet.com",
                "phone": "9876543210",
                "birthday": "1978-06-18",
            },
            headers=headers,
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unexpected error occurred."}


def test_update_contact_sqlalchemy_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    error_instance = SQLAlchemyError("Database error occurred.")

    with patch(
        "src.api.contacts.ContactsService.update_by_id", side_effect=error_instance
    ):
        response = client.patch(
            "/api/contacts/1",
            json={
                "first_name": "Bruce",
                "last_name": "Wayne",
                "email": "bruce@wayne.com",
                "phone": "1234567890",
                "birthday": "1985-02-19",
            },
            headers=headers,
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Database error occurred."}


def test_update_contact_unexpected_error(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    error_instance = Exception("Unexpected error occurred.")

    with patch(
        "src.api.contacts.ContactsService.update_by_id", side_effect=error_instance
    ):
        response = client.patch(
            "/api/contacts/1",
            json={
                "first_name": "Clark",
                "last_name": "Kent",
                "email": "clark@dailyplanet.com",
                "phone": "9876543210",
                "birthday": "1978-06-18",
            },
            headers=headers,
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unexpected error occurred."}


def test_update_contact_success(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    contact_data = {
        "id": 1,
        "first_name": "Peter",
        "last_name": "Parker",
        "email": "peter@spiderman.com",
        "phone": "1231231234",
        "birthday": "1990-07-02",
    }

    with patch(
        "src.api.contacts.ContactsService.update_by_id", return_value=contact_data
    ):
        response = client.patch("/api/contacts/1", json=contact_data, headers=headers)

    assert response.status_code == 200
    assert response.json() == contact_data


def test_update_contact_not_found(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    with patch("src.api.contacts.ContactsService.update_by_id", return_value=None):
        response = client.get("/api/contacts/10", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}
