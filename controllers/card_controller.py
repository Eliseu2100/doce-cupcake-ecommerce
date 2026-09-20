"""Camada Controller — cartões salvos pelo usuário."""
from flask import Blueprint, jsonify, request, session
from models.card_model import CardModel

card_bp = Blueprint("cards", __name__, url_prefix="/api")


def _require_login():
    return session.get("user_id")


@card_bp.route("/cards", methods=["GET"])
def list_cards():
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login para ver seus cartões."}), 401
    return jsonify(CardModel.list_by_user(user_id))


@card_bp.route("/cards", methods=["POST"])
def create_card():
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login para cadastrar um cartão."}), 401

    payload = request.get_json(silent=True) or {}
    try:
        card = CardModel.create(
            user_id=user_id,
            card_number=payload.get("card_number"),
            card_name=payload.get("card_name"),
            expiry=payload.get("expiry"),
            is_default=bool(payload.get("is_default")),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify(card), 201


@card_bp.route("/cards/<int:card_id>", methods=["DELETE"])
def delete_card(card_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login."}), 401
    CardModel.delete(card_id, user_id)
    return jsonify({"ok": True})
