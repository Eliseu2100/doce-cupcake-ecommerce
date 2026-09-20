"""Configuração compartilhada dos testes (fixtures do pytest)."""
import os
import tempfile
import pytest

os.environ.setdefault("APP_ENCRYPTION_KEY", "chave-de-teste-nao-use-em-producao")


@pytest.fixture
def app():
    """Cria a aplicação com um banco SQLite temporário, isolado por teste."""
    from app import create_app
    import config

    db_fd, db_path = tempfile.mkstemp()
    config.Config.DATABASE_PATH = db_path

    app = create_app()
    app.config.update(TESTING=True)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def featured_product(client):
    return client.get("/api/products/featured").get_json()


@pytest.fixture
def registered_user(client):
    """Cadastra e já deixa logado um usuário de teste."""
    payload = {
        "name": "Usuária de Teste",
        "email": "teste@doce-cupcake.dev",
        "password": "Senha1234",
        "phone": "11987654321",
        "accepted_privacy": True,
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    return res.get_json()


@pytest.fixture
def address(client, registered_user):
    res = client.post("/api/addresses", json={
        "label": "Casa", "zip_code": "01310100", "street": "Av Paulista",
        "number": "1000", "neighborhood": "Bela Vista", "city": "São Paulo", "state": "SP",
    })
    assert res.status_code == 201
    return res.get_json()
