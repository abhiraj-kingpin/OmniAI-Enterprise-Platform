def test_login_wrong_password_rejected(client):
    response = client.post("/api/auth/token", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_success_returns_bearer_token(client):
    response = client.post("/api/auth/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_user_with_valid_token(client):
    login = client.post("/api/auth/token", data={"username": "demo", "password": "demo123"})
    token = login.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "demo"


def test_rbac_denies_non_admin(client):
    login = client.post("/api/auth/token", data={"username": "demo", "password": "demo123"})
    token = login.json()["access_token"]

    response = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_rbac_allows_admin(client):
    login = client.post("/api/auth/token", data={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]

    response = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
