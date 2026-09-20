"""Camada Controller — consulta de CEP (ViaCEP / base dos Correios)."""
from flask import Blueprint, jsonify
from models.cep_lookup import CepLookup

cep_bp = Blueprint("cep", __name__, url_prefix="/api")


@cep_bp.route("/cep/<cep>")
def buscar_cep(cep):
    try:
        endereco = CepLookup.buscar(cep)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(endereco)
