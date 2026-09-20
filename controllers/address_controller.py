"""Camada Controller — endereços de entrega salvos pelo usuário."""
from flask import Blueprint, jsonify, request, session
from models.address_model import AddressModel

address_bp = Blueprint("addresses", __name__, url_prefix="/api")


def _require_login():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@address_bp.route("/addresses", methods=["GET"])
def list_addresses():
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login para ver seus endereços."}), 401
    return jsonify(AddressModel.list_by_user(user_id))


@address_bp.route("/addresses", methods=["POST"])
def create_address():
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login para cadastrar um endereço."}), 401

    payload = request.get_json(silent=True) or {}
    try:
        address = AddressModel.create(
            user_id=user_id,
            label=payload.get("label"),
            street=payload.get("street"),
            number=payload.get("number"),
            complement=payload.get("complement"),
            neighborhood=payload.get("neighborhood"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
            is_default=bool(payload.get("is_default")),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify(address), 201


@address_bp.route("/addresses/<int:address_id>", methods=["DELETE"])
def delete_address(address_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"erro": "Faça login."}), 401

    AddressModel.delete(address_id, user_id)
    return jsonify({"ok": True})
