"""
Camada Controller — endpoints de Categorias e Produtos.

Cada rota recebe a requisição HTTP, chama a camada Model correspondente
e devolve a resposta em JSON (aqui, a "View" consumida pelo JavaScript
do navegador).
"""
from flask import Blueprint, jsonify, request
from models.category_model import CategoryModel
from models.product_model import ProductModel

product_bp = Blueprint("products", __name__, url_prefix="/api")


@product_bp.route("/categories")
def list_categories():
    return jsonify(CategoryModel.get_all())


@product_bp.route("/products")
def list_products():
    category = request.args.get("category")
    return jsonify(ProductModel.get_all(category))


@product_bp.route("/products/featured")
def get_featured_product():
    product = ProductModel.get_featured()
    if product is None:
        return jsonify({"erro": "Nenhum produto em destaque."}), 404
    return jsonify(product)


@product_bp.route("/products/<int:product_id>")
def get_product(product_id):
    product = ProductModel.get_by_id(product_id)
    if product is None:
        return jsonify({"erro": "Produto não encontrado."}), 404
    return jsonify(product)
