"""Testes de cadastro, login, recuperação de senha e exclusão de conta."""


def test_register_requires_privacy_consent(client):
    res = client.post("/api/auth/register", json={
        "name": "Sem Consentimento", "email": "x@x.com", "password": "Senha1234", "phone": "11987654321",
    })
    assert res.status_code == 400


def test_register_rejects_weak_password(client):
    res = client.post("/api/auth/register", json={
        "name": "Senha Fraca", "email": "fraca@x.com", "password": "somente",
        "phone": "11987654321", "accepted_privacy": True,
    })
    assert res.status_code == 400


def test_register_and_login_flow(client, registered_user):
    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={
        "email": "teste@doce-cupcake.dev", "password": "Senha1234",
    })
    assert res.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_login_wrong_password_is_generic(client, registered_user):
    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={
        "email": "teste@doce-cupcake.dev", "password": "errada123",
    })
    assert res.status_code == 401
    assert "incorretos" in res.get_json()["erro"]


def test_login_rate_limit_blocks_brute_force(client, registered_user):
    client.post("/api/auth/logout")
    statuses = []
    for _ in range(10):
        res = client.post("/api/auth/login", json={
            "email": "teste@doce-cupcake.dev", "password": "errada",
        })
        statuses.append(res.status_code)
    assert 429 in statuses


def test_password_reset_flow(client, registered_user):
    res = client.post("/api/auth/forgot-password", json={"email": "teste@doce-cupcake.dev"})
    assert res.status_code == 200
    token = res.get_json()["reset_token"]

    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "NovaSenha123"})
    assert res.status_code == 200

    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={"email": "teste@doce-cupcake.dev", "password": "NovaSenha123"})
    assert res.status_code == 200

    # o mesmo token não pode ser reutilizado
    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "Outra1234"})
    assert res.status_code == 400


def test_forgot_password_unknown_email_is_generic(client):
    res = client.post("/api/auth/forgot-password", json={"email": "ninguem@x.com"})
    assert res.status_code == 404
    assert "reset_token" not in res.get_json()


def test_account_deletion(client, registered_user):
    res = client.delete("/api/auth/me")
    assert res.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
