"""Camada Model — lista de e-mails para newsletter (captação de leads)."""
from datetime import datetime
from models.user_model import EMAIL_REGEX
from models.database import get_db


class NewsletterModel:

    @staticmethod
    def subscribe(email):
        email = (email or "").strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValueError("E-mail inválido.")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM newsletter_subscribers WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            return {"email": email, "already_subscribed": True}

        db.execute(
            "INSERT INTO newsletter_subscribers (email, created_at) VALUES (?, ?)",
            (email, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return {"email": email, "already_subscribed": False}
