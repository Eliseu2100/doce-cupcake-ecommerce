"""Camada Controller — endpoints de Pedidos (carrinho / checkout)."""
from flask import Blueprint, jsonify, request, session
from models.order_model import OrderModel

order_bp = Blueprint("orders", __name__, url_prefix="/api")


@order_bp.route("/orders", methods=["POST"])
def create_order():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Faça login para finalizar o pedido."}), 401

    payload = request.get_json(silent=True) or {}
    items = payload.get("items", [])

    try:
        order = OrderModel.create_order(
            items,
            user_id=user_id,
            address_id=payload.get("address_id"),
            contact_phone=payload.get("contact_phone"),
            coupon_code=payload.get("coupon_code"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify(order), 201


@order_bp.route("/orders")
def list_my_orders():
    """Histórico de pedidos do usuário logado — tela 'Meus Pedidos'."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Faça login para ver seus pedidos."}), 401
    return jsonify(OrderModel.get_by_user(user_id))


@order_bp.route("/orders/<int:order_id>")
def get_order(order_id):
    user_id = session.get("user_id")
    order = OrderModel.get_by_id(order_id)
    if order is None or order.get("user_id") != user_id:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    return jsonify(order)
