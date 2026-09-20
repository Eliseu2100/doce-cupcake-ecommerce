"""Camada Controller — inscrição na newsletter (captação de leads)."""
from flask import Blueprint, jsonify, request
from models.newsletter_model import NewsletterModel
from models.coupon_model import CouponModel

newsletter_bp = Blueprint("newsletter", __name__, url_prefix="/api")


@newsletter_bp.route("/newsletter", methods=["POST"])
def subscribe():
    payload = request.get_json(silent=True) or {}
    try:
        result = NewsletterModel.subscribe(payload.get("email"))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    coupon = CouponModel.create_welcome_coupon(result["email"])
    result["coupon_code"] = coupon["code"]
    result["discount_percent"] = coupon["discount_percent"]

    return jsonify(result), 201

