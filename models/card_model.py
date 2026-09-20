"""
Camada Model — cartões salvos pelo usuário.

Nunca guardamos o número completo do cartão nem o CVV — só os 4
últimos dígitos, a bandeira, o nome impresso e a validade. Isso é o
suficiente para reconhecer o cartão numa próxima compra; para
confirmar o pagamento, o CVV é pedido de novo (é assim que funciona
até em sistemas reais de "cartão salvo").
"""
import re
from datetime import datetime
from models.database import get_db
from models.card_service import luhn_valido, identificar_bandeira

EXPIRY_REGEX = re.compile(r"^(0[1-9]|1[0-2])\/(\d{2})$")


class CardModel:

    @staticmethod
    def create(user_id, card_number, card_name, expiry, is_default=False):
        digits = re.sub(r"\D", "", card_number or "")

        if len(digits) < 13 or len(digits) > 19:
            raise ValueError("Número de cartão inválido.")
        if not luhn_valido(digits):
            raise ValueError("Número de cartão inválido (não passou na validação).")
        if not card_name or len(card_name.strip()) < 3:
            raise ValueError("Informe o nome impresso no cartão.")
        if not expiry or not EXPIRY_REGEX.match(expiry):
            raise ValueError("Validade inválida. Use o formato MM/AA.")

        brand = identificar_bandeira(digits)
        last4 = digits[-4:]

        db = get_db()
        if is_default:
            db.execute("UPDATE cards SET is_default = 0 WHERE user_id = ?", (user_id,))

        total_existentes = db.execute(
            "SELECT COUNT(*) AS total FROM cards WHERE user_id = ?", (user_id,)
        ).fetchone()["total"]
        if total_existentes == 0:
            is_default = True

        cursor = db.execute(
            """INSERT INTO cards (user_id, brand, last4, card_name, expiry, is_default, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, brand, last4, card_name.strip(), expiry, 1 if is_default else 0,
             datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return CardModel.get_by_id_for_user(cursor.lastrowid, user_id)

    @staticmethod
    def list_by_user(user_id):
        db = get_db()
        rows = db.execute(
            "SELECT * FROM cards WHERE user_id = ? ORDER BY is_default DESC, id DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id_for_user(card_id, user_id):
        db = get_db()
        row = db.execute(
            "SELECT * FROM cards WHERE id = ? AND user_id = ?", (card_id, user_id)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete(card_id, user_id):
        db = get_db()
        db.execute("DELETE FROM cards WHERE id = ? AND user_id = ?", (card_id, user_id))
        db.commit()
