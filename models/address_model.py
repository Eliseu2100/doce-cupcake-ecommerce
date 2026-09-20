"""Camada Model — endereços de entrega salvos pelo usuário."""
import re
from datetime import datetime
from models.database import get_db
from models.crypto_utils import encrypt_field, decrypt_field

ZIP_REGEX = re.compile(r"^\d{8}$")

# Campos com dado de localização exata (mais sensíveis) — gravados
# criptografados. Cidade e UF continuam em claro: são baixa sensibilidade
# isoladas e úteis para exibir/filtrar sem precisar descriptografar tudo.
_ENCRYPTED_FIELDS = ("street", "number", "complement", "neighborhood", "zip_code")


def _decrypt_row(row):
    address = dict(row)
    for field in _ENCRYPTED_FIELDS:
        address[field] = decrypt_field(address.get(field))
    return address


class AddressModel:

    @staticmethod
    def create(user_id, label, street, number, neighborhood, city, state,
               zip_code, complement=None, is_default=False):
        label = (label or "").strip() or "Endereço"
        street = (street or "").strip()
        number = (number or "").strip()
        complement = (complement or "").strip()
        neighborhood = (neighborhood or "").strip()
        city = (city or "").strip()
        state = (state or "").strip().upper()
        zip_digits = re.sub(r"\D", "", zip_code or "")

        if not street or not number or not neighborhood or not city:
            raise ValueError("Preencha rua, número, bairro e cidade.")
        if len(state) != 2:
            raise ValueError("Informe a UF do estado (2 letras), ex: SP.")
        if not ZIP_REGEX.match(zip_digits):
            raise ValueError("CEP inválido. Informe os 8 dígitos.")

        db = get_db()

        if is_default:
            db.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))

        # Primeiro endereço do usuário vira padrão automaticamente
        total_existentes = db.execute(
            "SELECT COUNT(*) AS total FROM addresses WHERE user_id = ?", (user_id,)
        ).fetchone()["total"]
        if total_existentes == 0:
            is_default = True

        cursor = db.execute(
            """INSERT INTO addresses
               (user_id, label, street, number, complement, neighborhood, city, state, zip_code, is_default, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, label, encrypt_field(street), encrypt_field(number), encrypt_field(complement),
             encrypt_field(neighborhood), city, state, encrypt_field(zip_digits),
             1 if is_default else 0, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()

        return AddressModel.get_by_id_for_user(cursor.lastrowid, user_id)

    @staticmethod
    def list_by_user(user_id):
        db = get_db()
        rows = db.execute(
            "SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC",
            (user_id,),
        ).fetchall()
        return [_decrypt_row(row) for row in rows]

    @staticmethod
    def get_by_id_for_user(address_id, user_id):
        """Busca um endereço garantindo que ele pertence ao usuário logado
        — evita que alguém acesse ou use o endereço de outra pessoa."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM addresses WHERE id = ? AND user_id = ?", (address_id, user_id)
        ).fetchone()
        return _decrypt_row(row) if row else None

    @staticmethod
    def delete(address_id, user_id):
        db = get_db()
        # Pedidos antigos guardam seu próprio "retrato" do endereço
        # (campos delivery_*), então não dependem mais desta linha —
        # só soltamos a referência antes de apagar, para não violar a
        # integridade referencial.
        db.execute(
            "UPDATE orders SET address_id = NULL WHERE address_id = ? AND user_id = ?",
            (address_id, user_id),
        )
        db.execute("DELETE FROM addresses WHERE id = ? AND user_id = ?", (address_id, user_id))
        db.commit()
