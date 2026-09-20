"""Camada Model — regras de negócio e persistência de Pedidos."""
import re
from datetime import datetime
from models.database import get_db
from models.product_model import ProductModel
from models.address_model import AddressModel
from models.crypto_utils import encrypt_field, decrypt_field
from models.coupon_model import CouponModel

PHONE_REGEX = re.compile(r"^\d{10,11}$")


class OrderModel:

    @staticmethod
    def create_order(items, user_id, address_id, contact_phone, coupon_code=None):
        """
        Cria um pedido a partir de uma lista de itens no formato:
            [{"product_id": int, "size": str|None, "quantity": int}, ...]

        Exige também o endereço de entrega (já salvo pelo usuário) e um
        telefone de contato para aquele pedido específico. O endereço é
        gravado como uma "fotografia" (snapshot) no próprio pedido, para
        que continue correto mesmo se o usuário editar ou apagar o
        endereço salvo depois.

        Se um cupom válido for informado, o desconto é aplicado aqui
        (nunca confiando em nenhum valor de desconto vindo do
        navegador) — mas o cupom só é marcado como "usado" quando o
        pagamento é confirmado (ver PaymentModel), para não perder o
        cupom em carrinhos abandonados.

        Todo o cálculo de preço é refeito aqui, a partir do banco de
        dados — o "processamento de dados" pedido no exercício.
        Lança ValueError se algum dado for inválido.
        """
        if not items:
            raise ValueError("O pedido precisa ter pelo menos um item.")

        phone_digits = re.sub(r"\D", "", contact_phone or "")
        if not PHONE_REGEX.match(phone_digits):
            raise ValueError("Informe um telefone de contato válido para este pedido.")

        address = AddressModel.get_by_id_for_user(address_id, user_id)
        if address is None:
            raise ValueError("Selecione um endereço de entrega válido.")

        coupon = None
        if coupon_code:
            coupon = CouponModel.validate(coupon_code)  # lança ValueError se inválido/usado

        db = get_db()
        order_items = []
        subtotal_total = 0.0

        for item in items:
            product_id = item.get("product_id")
            size = item.get("size")
            try:
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError):
                raise ValueError("Quantidade inválida para um dos itens.")

            if quantity < 1:
                raise ValueError("Quantidade inválida para um dos itens.")

            product = ProductModel.get_by_id(product_id)
            if product is None:
                raise ValueError(f"Produto {product_id} não encontrado.")

            unit_price = ProductModel.get_price_for(product_id, size)
            if unit_price is None:
                raise ValueError(f"Tamanho inválido para o produto '{product['name']}'.")

            subtotal = round(unit_price * quantity, 2)
            subtotal_total += subtotal

            order_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "size": size,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })

        subtotal_total = round(subtotal_total, 2)
        discount_amount = round(subtotal_total * (coupon["discount_percent"] / 100), 2) if coupon else 0.0
        total = round(subtotal_total - discount_amount, 2)
        created_at = datetime.now().isoformat(timespec="seconds")

        cursor = db.execute(
            """INSERT INTO orders
               (user_id, created_at, status, total, coupon_code, discount_amount,
                contact_phone, address_id,
                delivery_label, delivery_street, delivery_number, delivery_complement,
                delivery_neighborhood, delivery_city, delivery_state, delivery_zip_code)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, created_at, "pendente", total, coupon["code"] if coupon else None, discount_amount,
             encrypt_field(phone_digits), address_id,
             address["label"], encrypt_field(address["street"]), encrypt_field(address["number"]),
             encrypt_field(address["complement"]), encrypt_field(address["neighborhood"]),
             address["city"], address["state"], encrypt_field(address["zip_code"])),
        )
        order_id = cursor.lastrowid

        for order_item in order_items:
            db.execute(
                """INSERT INTO order_items
                   (order_id, product_id, size_label, quantity, unit_price, subtotal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    order_id,
                    order_item["product_id"],
                    order_item["size"],
                    order_item["quantity"],
                    order_item["unit_price"],
                    order_item["subtotal"],
                ),
            )

        db.commit()

        return {
            "id": order_id,
            "created_at": created_at,
            "status": "pendente",
            "subtotal": subtotal_total,
            "discount_amount": discount_amount,
            "coupon_code": coupon["code"] if coupon else None,
            "total": total,
            "items": order_items,
            "contact_phone": phone_digits,
            "delivery_address": address,
        }

    @staticmethod
    def get_by_id(order_id):
        db = get_db()
        order_row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order_row is None:
            return None
        return OrderModel._decorate(order_row, db)

    @staticmethod
    def get_by_user(user_id):
        """Histórico de pedidos do usuário, mais recentes primeiro —
        usado na tela 'Meus Pedidos'."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()
        return [OrderModel._decorate(row, db, include_items=False) for row in rows]

    @staticmethod
    def _decorate(order_row, db, include_items=True):
        order = dict(order_row)
        order["contact_phone"] = decrypt_field(order["contact_phone"])
        order["delivery_street"] = decrypt_field(order["delivery_street"])
        order["delivery_number"] = decrypt_field(order["delivery_number"])
        order["delivery_complement"] = decrypt_field(order["delivery_complement"])
        order["delivery_neighborhood"] = decrypt_field(order["delivery_neighborhood"])
        order["delivery_zip_code"] = decrypt_field(order["delivery_zip_code"])

        if include_items:
            item_rows = db.execute(
                """SELECT oi.*, p.name AS product_name
                   FROM order_items oi
                   JOIN products p ON p.id = oi.product_id
                   WHERE oi.order_id = ?""",
                (order["id"],),
            ).fetchall()
            order["items"] = [dict(row) for row in item_rows]
        else:
            count_row = db.execute(
                "SELECT COUNT(*) AS total FROM order_items WHERE order_id = ?", (order["id"],)
            ).fetchone()
            order["item_count"] = count_row["total"]

        return order
