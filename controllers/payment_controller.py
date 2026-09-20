"""Camada Controller — processamento de pagamento de um pedido."""
from flask import Blueprint, jsonify, request, session
from models.payment_model import PaymentModel
from models.order_model import OrderModel

payment_bp = Blueprint("payments", __name__, url_prefix="/api")


@payment_bp.route("/orders/<int:order_id>/pagamento", methods=["POST"])
def pay_order(order_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Você precisa estar logado para pagar um pedido."}), 401

    order = OrderModel.get_by_id(order_id)
    if order is None or order.get("user_id") != user_id:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    payload = request.get_json(silent=True) or {}

    try:
        result = PaymentModel.process(
            order_id=order_id,
            user_id=user_id,
            method=payload.get("method"),
            card_id=payload.get("card_id"),
            card_number=payload.get("card_number"),
            card_name=payload.get("card_name"),
            expiry=payload.get("expiry"),
            cvv=payload.get("cvv"),
            save_card=bool(payload.get("save_card")),
            installments=payload.get("installments", 1),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify(result), 201
