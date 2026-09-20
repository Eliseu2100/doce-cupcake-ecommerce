"""
Camada Model — tokens de "esqueci minha senha".

Como o projeto não tem um serviço de e-mail configurado (SMTP, SendGrid
etc.), o link de redefinição é devolvido diretamente na resposta da
API e mostrado na própria tela — isso é deixado bem explícito na
interface, para não passar a falsa impressão de que um e-mail foi
enviado de verdade. O mecanismo em si (token aleatório, validade de 1
hora, uso único) é o mesmo que um sistema real usaria por trás do
e-mail.
"""
import secrets
from datetime import datetime, timedelta
from models.database import get_db

TOKEN_VALIDITY_MINUTES = 60


class PasswordResetModel:

    @staticmethod
    def create_token(user_id):
        db = get_db()
        # Invalida tokens antigos ainda não usados desse usuário, para
        # não deixar vários links de redefinição válidos ao mesmo tempo.
        db.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0",
            (user_id,),
        )

        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(minutes=TOKEN_VALIDITY_MINUTES)).isoformat(timespec="seconds")

        db.execute(
            """INSERT INTO password_reset_tokens (user_id, token, expires_at, used, created_at)
               VALUES (?, ?, ?, 0, ?)""",
            (user_id, token, expires_at, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return token

    @staticmethod
    def get_valid_token(token):
        """Retorna a linha do token se ele existir, não tiver sido usado
        e ainda não tiver expirado. None caso contrário."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0",
            (token,),
        ).fetchone()

        if row is None:
            return None
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            return None
        return dict(row)

    @staticmethod
    def mark_used(token):
        db = get_db()
        db.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
        db.commit()
