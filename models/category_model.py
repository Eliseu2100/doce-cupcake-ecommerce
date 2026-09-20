"""Camada Model — regras de acesso a dados de Categorias."""
from models.database import get_db


class CategoryModel:

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("SELECT id, slug, name FROM categories ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_slug(slug):
        db = get_db()
        row = db.execute(
            "SELECT id, slug, name FROM categories WHERE slug = ?", (slug,)
        ).fetchone()
        return dict(row) if row else None
