"""Camada Model — regras de acesso a dados de Usuários (cadastro/login)."""
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db
from models.crypto_utils import encrypt_field, decrypt_field

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\d{10,11}$")  # DDD + número, só dígitos
PASSWORD_HAS_LETTER = re.compile(r"[A-Za-z]")
PASSWORD_HAS_DIGIT = re.compile(r"\d")


class UserModel:

    @staticmethod
    def create(name, email, password, phone):
        """Cria um usuário novo. Lança ValueError em caso de dado inválido
        ou e-mail já cadastrado. A senha nunca é armazenada em texto puro —
        só o hash (gerado pelo Werkzeug). O telefone é gravado criptografado
        (models/crypto_utils.py)."""
        name = (name or "").strip()
        email = (email or "").strip().lower()
        phone_digits = re.sub(r"\D", "", phone or "")
        password = password or ""

        if len(name) < 2:
            raise ValueError("Informe seu nome completo.")
        if not EMAIL_REGEX.match(email):
            raise ValueError("E-mail inválido.")
        if len(password) < 8 or not PASSWORD_HAS_LETTER.search(password) or not PASSWORD_HAS_DIGIT.search(password):
            raise ValueError("A senha precisa ter pelo menos 8 caracteres, com letras e números.")
        if not PHONE_REGEX.match(phone_digits):
            raise ValueError("Telefone inválido. Informe DDD + número (10 ou 11 dígitos).")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ValueError("Já existe uma conta cadastrada com esse e-mail.")

        password_hash = generate_password_hash(password)
        created_at = datetime.now().isoformat(timespec="seconds")

        cursor = db.execute(
            "INSERT INTO users (name, email, phone, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, encrypt_field(phone_digits), password_hash, created_at),
        )
        db.commit()

        return {"id": cursor.lastrowid, "name": name, "email": email, "phone": phone_digits}

    @staticmethod
    def authenticate(email, password):
        """Confere e-mail/senha. Retorna o usuário (sem o hash) se estiver
        correto, ou None caso contrário. A mensagem de erro no Controller é
        sempre genérica ('e-mail ou senha incorretos'), para não revelar a
        quem está tentando adivinhar se o e-mail existe ou não na base."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)
        ).fetchone()

        if row is None:
            return None
        if not check_password_hash(row["password_hash"], password or ""):
            return None

        return {"id": row["id"], "name": row["name"], "email": row["email"], "phone": decrypt_field(row["phone"])}

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute(
            "SELECT id, name, email, phone FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        user = dict(row)
        user["phone"] = decrypt_field(user["phone"])
        return user

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute(
            "SELECT id, name, email FROM users WHERE email = ?", ((email or "").strip().lower(),)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_password(user_id, new_password):
        new_password = new_password or ""
        if len(new_password) < 8 or not PASSWORD_HAS_LETTER.search(new_password) or not PASSWORD_HAS_DIGIT.search(new_password):
            raise ValueError("A senha precisa ter pelo menos 8 caracteres, com letras e números.")
        db = get_db()
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), user_id),
        )
        db.commit()

    @staticmethod
    def delete_account(user_id):
        """Exclusão de conta (direito de exclusão da LGPD). Endereços e
        cartões salvos são apagados; os pedidos já feitos são mantidos
        para fins fiscais/contábeis, mas desvinculados do usuário
        (user_id vira NULL) — é a mesma prática comum em e-commerces
        reais: anonimizar em vez de apagar o histórico de transações."""
        db = get_db()
        db.execute("UPDATE orders SET address_id = NULL WHERE user_id = ?", (user_id,))
        db.execute("UPDATE orders SET user_id = NULL WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM addresses WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM cards WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
