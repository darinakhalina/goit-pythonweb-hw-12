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
