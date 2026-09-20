"""Camada Controller — consulta de cupom de desconto (só leitura)."""
from flask import Blueprint, jsonify
from models.coupon_model import CouponModel

coupon_bp = Blueprint("coupons", __name__, url_prefix="/api")


@coupon_bp.route("/coupons/<code>")
def check_coupon(code):
    """Só confere se o cupom é válido e devolve o desconto — não marca
    como usado (isso só acontece quando o pagamento é confirmado)."""
    try:
        coupon = CouponModel.validate(code)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"code": coupon["code"], "discount_percent": coupon["discount_percent"]})
