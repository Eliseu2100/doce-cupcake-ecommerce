"""Testes de carrinho/pedido: cálculo de preço, endereço obrigatório e cupom."""
import pytest


def create_order(client, product_id, address_id, coupon_code=None, quantity=1, size=None):
    payload = {
        "items": [{"product_id": product_id, "size": size, "quantity": quantity}],
        "address_id": address_id,
        "contact_phone": "11912345678",
    }
    if coupon_code:
        payload["coupon_code"] = coupon_code
    return client.post("/api/orders", json=payload)


def test_order_requires_login(client, featured_product):
    res = client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "quantity": 1}],
    })
    assert res.status_code == 401


def test_order_requires_address(client, registered_user, featured_product):
    res = client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "quantity": 1}],
        "contact_phone": "11912345678",
    })
    assert res.status_code == 400


def test_order_price_is_recalculated_server_side(client, registered_user, address, featured_product):
    """O preço do item vem sempre do banco — mesmo que o front mande outro valor."""
    res = client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "size": "P", "quantity": 2, "unit_price": 0.01}],
        "address_id": address["id"],
        "contact_phone": "11912345678",
    })
    assert res.status_code == 201
    order = res.get_json()
    expected_unit_price = next(s["price"] for s in featured_product["sizes"] if s["label"] == "P")
    assert order["items"][0]["unit_price"] == expected_unit_price
    assert order["total"] == round(expected_unit_price * 2, 2)


def test_order_snapshot_survives_address_edit(client, registered_user, address, featured_product):
    res = create_order(client, featured_product["id"], address["id"])
    order_id = res.get_json()["id"]

    client.delete(f"/api/addresses/{address['id']}")

    res = client.get(f"/api/orders/{order_id}")
    assert res.status_code == 200
    assert res.get_json()["delivery_street"] == "Av Paulista"


def test_coupon_from_newsletter_applies_discount_once(client, registered_user, address, featured_product):
    res = client.post("/api/newsletter", json={"email": "teste@doce-cupcake.dev"})
    assert res.status_code == 201
    coupon_code = res.get_json()["coupon_code"]

    res = create_order(client, featured_product["id"], address["id"], coupon_code=coupon_code)
    assert res.status_code == 201
    order = res.get_json()
    assert order["discount_amount"] > 0

    client.post(f"/api/orders/{order['id']}/pagamento", json={"method": "pix"})

    # o mesmo cupom não pode ser usado de novo depois de pago
    res2 = client.get(f"/api/coupons/{coupon_code}")
    assert res2.status_code == 400


def test_orders_list_only_shows_own_orders(client, registered_user, address, featured_product):
    create_order(client, featured_product["id"], address["id"])
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={
        "name": "Outra Pessoa", "email": "outra@doce-cupcake.dev", "password": "Senha1234",
        "phone": "11987654322", "accepted_privacy": True,
    })
    res = client.get("/api/orders")
    assert res.status_code == 200
    assert res.get_json() == []
