def test_healthchecker_success(client):
    response = client.get("/api/healthchecker")
    data = response.json()

    assert response.status_code == 200, response.text
    assert "message" in data, "Message key not found"
    assert data["message"] == "Welcome to FastAPI!"


def test_healthchecker_success_fail(client_fail_healthchecker):
    response = client_fail_healthchecker.get("api/healthchecker")
    data = response.json()

    assert response.status_code == 500, response.text
    assert "detail" in data
