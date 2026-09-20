"""
Camada Model — cupons de desconto.

Cada e-mail cadastrado na newsletter ganha um cupom de uso único
(hoje, sempre 10% — o mesmo valor anunciado na seção de newsletter do
site). O cupom só é "gasto" de fato quando o pedido em que foi usado
é pago (não quando é só criado), para não perder o cupom em carrinhos
abandonados.
"""
import random
import string
from datetime import datetime
from models.database import get_db

WELCOME_DISCOUNT_PERCENT = 10.0


def _gerar_codigo():
    sufixo = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"BEMVINDO-{sufixo}"


class CouponModel:

    @staticmethod
    def create_welcome_coupon(email):
        """Gera um cupom de boas-vindas para quem assina a newsletter.
        Se o e-mail já tiver um cupom de boas-vindas, devolve o mesmo
        (evita gerar cupons infinitos para quem se cadastra de novo)."""
        db = get_db()
        existing = db.execute(
            "SELECT * FROM coupons WHERE email = ? AND code LIKE 'BEMVINDO-%'", (email,)
        ).fetchone()
        if existing:
            return dict(existing)

        code = _gerar_codigo()
        db.execute(
            """INSERT INTO coupons (code, discount_percent, email, used, created_at)
               VALUES (?, ?, ?, 0, ?)""",
            (code, WELCOME_DISCOUNT_PERCENT, email, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return CouponModel.get_by_code(code)

    @staticmethod
    def get_by_code(code):
        db = get_db()
        row = db.execute("SELECT * FROM coupons WHERE code = ?", ((code or "").strip().upper(),)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def validate(code):
        """Confere se um cupom existe e ainda não foi usado. Lança
        ValueError com uma mensagem amigável quando não é válido."""
        coupon = CouponModel.get_by_code(code)
        if coupon is None:
            raise ValueError("Cupom não encontrado.")
        if coupon["used"]:
            raise ValueError("Esse cupom já foi utilizado.")
        return coupon

    @staticmethod
    def mark_used(code, order_id):
        db = get_db()
        db.execute(
            "UPDATE coupons SET used = 1, used_by_order_id = ? WHERE code = ?",
            (order_id, (code or "").strip().upper()),
        )
        db.commit()
