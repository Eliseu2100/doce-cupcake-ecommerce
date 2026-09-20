"""Testes de endereços/cartões salvos: propriedade, criptografia e exclusão."""
import sqlite3


def test_cannot_access_another_users_address(client, registered_user, address):
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={
        "name": "Outra Pessoa", "email": "outra2@doce-cupcake.dev", "password": "Senha1234",
        "phone": "11987654322", "accepted_privacy": True,
    })
    res = client.get("/api/addresses")
    assert res.status_code == 200
    assert res.get_json() == []  # não vê o endereço da outra pessoa


def test_address_fields_are_encrypted_at_rest(app, client, registered_user, address):
    db = sqlite3.connect(app.config["DATABASE_PATH"])
    row = db.execute("SELECT street, city FROM addresses WHERE id = ?", (address["id"],)).fetchone()
    db.close()
    assert row[0] != "Av Paulista"  # criptografado no banco
    assert row[1] == "São Paulo"    # cidade fica em claro (baixa sensibilidade)
    assert address["street"] == "Av Paulista"  # mas a API decodifica certo


def test_phone_is_encrypted_at_rest(app, client, registered_user):
    db = sqlite3.connect(app.config["DATABASE_PATH"])
    row = db.execute("SELECT phone FROM users WHERE email = ?", ("teste@doce-cupcake.dev",)).fetchone()
    db.close()
    assert row[0] != "11987654321"


def test_delete_address_linked_to_past_order_does_not_break(client, registered_user, address, featured_product):
    client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "quantity": 1}],
        "address_id": address["id"],
        "contact_phone": "11912345678",
    })
    res = client.delete(f"/api/addresses/{address['id']}")
    assert res.status_code == 200
    assert client.get("/api/addresses").get_json() == []


def test_account_deletion_anonymizes_orders_instead_of_deleting_them(app, client, registered_user, address, featured_product):
    order = client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "quantity": 1}],
        "address_id": address["id"],
        "contact_phone": "11912345678",
    }).get_json()
    client.post(f"/api/orders/{order['id']}/pagamento", json={"method": "pix"})

    client.delete("/api/auth/me")

    db = sqlite3.connect(app.config["DATABASE_PATH"])
    row = db.execute("SELECT user_id, status FROM orders WHERE id = ?", (order["id"],)).fetchone()
    db.close()
    assert row[0] is None       # desvinculado do usuário
    assert row[1] == "pago"     # mas o pedido em si continua existindo
