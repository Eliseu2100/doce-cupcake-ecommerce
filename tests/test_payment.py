"""Testes de pagamento: cartão (Luhn/bandeira/parcelas), cartão salvo, Pix e boleto."""
import pytest


def create_paid_order(client, address, featured_product):
    res = client.post("/api/orders", json={
        "items": [{"product_id": featured_product["id"], "quantity": 1}],
        "address_id": address["id"],
        "contact_phone": "11912345678",
    })
    return res.get_json()["id"]


def test_card_with_invalid_luhn_is_rejected(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id}/pagamento", json={
        "method": "cartao", "card_name": "TESTE", "card_number": "4111111111111112",
        "expiry": "12/29", "cvv": "123",
    })
    assert res.status_code == 400


def test_card_brand_detection_and_installments(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id}/pagamento", json={
        "method": "cartao", "card_name": "TESTE VISA", "card_number": "4111111111111111",
        "expiry": "12/29", "cvv": "123", "installments": 6,
    })
    assert res.status_code == 201
    result = res.get_json()
    assert result["card_brand"] == "visa"
    assert result["installments"] == 6
    assert result["amount"] > 0


def test_amex_requires_4_digit_cvv(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id}/pagamento", json={
        "method": "cartao", "card_name": "TESTE AMEX", "card_number": "371449635398431",
        "expiry": "12/29", "cvv": "123",  # só 3 dígitos, Amex exige 4
    })
    assert res.status_code == 400


def test_saved_card_can_be_reused_with_cvv_only(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    client.post(f"/api/orders/{order_id}/pagamento", json={
        "method": "cartao", "card_name": "TESTE VISA", "card_number": "4111111111111111",
        "expiry": "12/29", "cvv": "123", "save_card": True,
    })

    cards = client.get("/api/cards").get_json()
    assert len(cards) == 1
    assert cards[0]["last4"] == "1111"

    order_id_2 = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id_2}/pagamento", json={
        "method": "cartao", "card_id": cards[0]["id"], "cvv": "123",
    })
    assert res.status_code == 201


def test_pix_generates_valid_emv_code(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id}/pagamento", json={"method": "pix"})
    assert res.status_code == 201
    assert res.get_json()["pix_copia_cola"].startswith("0002")


def test_boleto_has_47_digits(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res = client.post(f"/api/orders/{order_id}/pagamento", json={"method": "boleto"})
    assert res.status_code == 201
    codigo = res.get_json()["boleto_barcode"].replace(".", "").replace(" ", "")
    assert len(codigo) == 47


def test_cannot_pay_same_order_twice(client, registered_user, address, featured_product):
    order_id = create_paid_order(client, address, featured_product)
    res1 = client.post(f"/api/orders/{order_id}/pagamento", json={"method": "pix"})
    assert res1.status_code == 201
    res2 = client.post(f"/api/orders/{order_id}/pagamento", json={"method": "pix"})
    assert res2.status_code == 400
