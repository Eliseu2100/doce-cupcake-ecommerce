"""Testes das páginas HTML (a aplicação sobe e todas as rotas respondem)."""
import pytest

PUBLIC_PAGES = [
    "/", "/login", "/cadastro", "/entrega", "/pagamento",
    "/esqueci-senha", "/redefinir-senha", "/privacidade", "/minha-conta",
    "/robots.txt", "/sitemap.xml",
]


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_page_returns_200(client, path):
    assert client.get(path).status_code == 200


def test_404_page_is_branded(client):
    res = client.get("/pagina-que-nao-existe")
    assert res.status_code == 404
    assert "Ops, esse cupcake sumiu" in res.get_data(as_text=True)


def test_security_headers_present(client):
    res = client.get("/")
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src" in res.headers.get("Content-Security-Policy", "")
