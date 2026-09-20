"""
Camada Model — infraestrutura de persistência.

Este módulo cuida apenas de abrir/fechar a conexão SQLite e garantir
que o schema exista. As regras de negócio de cada entidade ficam nos
outros arquivos da camada Model (category_model, product_model,
order_model) — aqui é só o "cano" de acesso ao banco.
"""
import sqlite3
from flask import g, current_app


def get_db():
    """Retorna a conexão SQLite da requisição atual, criando uma se
    ainda não existir (uma conexão por requisição, padrão do Flask)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """Fecha a conexão ao final da requisição (chamado pelo Flask via
    teardown_appcontext)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Cria as tabelas a partir do schema.sql e popula dados de
    demonstração na primeira execução da aplicação."""
    db = sqlite3.connect(app.config["DATABASE_PATH"])
    db.row_factory = sqlite3.Row

    with open(app.config["SCHEMA_PATH"], "r", encoding="utf-8") as f:
        db.executescript(f.read())

    total_categorias = db.execute("SELECT COUNT(*) AS total FROM categories").fetchone()["total"]
    if total_categorias == 0:
        _seed(db)

    db.commit()
    db.close()


def _seed(db):
    """Popula o banco com o cardápio inicial do ateliê."""
    categorias = [
        ("cupcakes", "Cupcakes"),
        ("bolos", "Bolos"),
        ("tortas", "Tortas"),
        ("sorvetes", "Sorvetes"),
    ]
    db.executemany("INSERT INTO categories (slug, name) VALUES (?, ?)", categorias)

    cat_ids = {row["slug"]: row["id"] for row in db.execute("SELECT id, slug FROM categories")}

    # (slug_categoria, nome, descrição, preço, ícone, destaque, rating, avaliações)
    produtos = [
        ("cupcakes", "Donuts recheados", "Caixa com 5 unidades, recheios variados", 35.00, "donut", 0, 4.8, 512),
        ("cupcakes", "Cookies gourmet", "Unidade, recheado com gotas de chocolate", 5.00, "cookie", 0, 4.7, 233),
        ("cupcakes", "Cupcake de Cereja",
         "Caixa de cupcakes de cereja sem glúten e sem lactose, feitos com ingredientes "
         "selecionados e cobertura de chantininho batido na hora.", 39.99, "cupcake_cherry", 1, 5.0, 2437),
        ("bolos", "Brownies artesanais", "Caixa com 5 unidades, chocolate 70%", 25.00, "brownie", 0, 4.9, 401),
        ("bolos", "Bolo de chocolate", "Redondo, serve até 10 pessoas", 45.00, "cake_choc", 0, 4.8, 188),
        ("tortas", "Torta de morango", "Fatia individual, base amanteigada", 9.99, "pie_strawberry", 0, 4.6, 322),
        ("tortas", "Torta de limão", "Base crocante, cobertura de merengue", 32.00, "pie_lemon", 0, 4.7, 150),
        ("sorvetes", "Sorvete trio", "Baunilha, chocolate e morango", 18.00, "icecream", 0, 4.5, 96),
    ]

    for slug, nome, desc, preco, icone, destaque, rating, avaliacoes in produtos:
        db.execute(
            """INSERT INTO products
               (category_id, name, description, price, icon, featured, rating, review_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (cat_ids[slug], nome, desc, preco, icone, destaque, rating, avaliacoes),
        )

    produto_destaque_id = db.execute(
        "SELECT id FROM products WHERE name = 'Cupcake de Cereja'"
    ).fetchone()["id"]

    tamanhos = [
        (produto_destaque_id, "P", 39.99),
        (produto_destaque_id, "M", 54.99),
        (produto_destaque_id, "G", 69.99),
    ]
    db.executemany(
        "INSERT INTO product_sizes (product_id, label, price) VALUES (?, ?, ?)",
        tamanhos,
    )
