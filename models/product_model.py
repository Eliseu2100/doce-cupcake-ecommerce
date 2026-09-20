"""Camada Model — regras de acesso a dados de Produtos."""
from models.database import get_db


class ProductModel:

    @staticmethod
    def get_all(category_slug=None):
        db = get_db()
        base_query = """
            SELECT p.*, c.slug AS category_slug, c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
        """
        if category_slug and category_slug != "todos":
            rows = db.execute(base_query + " WHERE c.slug = ? ORDER BY p.id", (category_slug,)).fetchall()
        else:
            rows = db.execute(base_query + " ORDER BY p.id").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(product_id):
        db = get_db()
        row = db.execute(
            """SELECT p.*, c.slug AS category_slug, c.name AS category_name
               FROM products p
               JOIN categories c ON c.id = p.category_id
               WHERE p.id = ?""",
            (product_id,),
        ).fetchone()

        if row is None:
            return None

        product = dict(row)
        sizes = db.execute(
            "SELECT label, price FROM product_sizes WHERE product_id = ?",
            (product_id,),
        ).fetchall()
        product["sizes"] = [dict(size) for size in sizes]
        return product

    @staticmethod
    def get_featured():
        db = get_db()
        row = db.execute("SELECT id FROM products WHERE featured = 1 LIMIT 1").fetchone()
        return ProductModel.get_by_id(row["id"]) if row else None

    @staticmethod
    def get_price_for(product_id, size_label=None):
        """Calcula o preço correto no lado do servidor.

        Regra de negócio importante: o preço NUNCA vem do cliente,
        só o id do produto e, opcionalmente, o tamanho escolhido.
        Isso evita que alguém manipule o preço pelo JavaScript do navegador.
        """
        db = get_db()
        if size_label:
            row = db.execute(
                "SELECT price FROM product_sizes WHERE product_id = ? AND label = ?",
                (product_id, size_label),
            ).fetchone()
            if row:
                return row["price"]

        row = db.execute("SELECT price FROM products WHERE id = ?", (product_id,)).fetchone()
        return row["price"] if row else None
