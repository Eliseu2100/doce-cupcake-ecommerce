"""
Camada Controller — cadastro, login, sessão, recuperação de senha e
exclusão de conta.

A sessão é controlada pelo mecanismo de sessão do próprio Flask
(cookie assinado, HttpOnly + SameSite — ver config.py). Aqui guardamos
só o "user_id" na sessão — nenhum dado sensível fica no cookie.

Login e cadastro têm limite de tentativas por IP (Flask-Limiter) para
dificultar ataques de força bruta / credential stuffing.
"""
from flask import Blueprint, jsonify, request, session
from models.user_model import UserModel
from models.address_model import AddressModel
from models.password_reset_model import PasswordResetModel
from extensions import limiter

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    payload = request.get_json(silent=True) or {}

    if not payload.get("accepted_privacy"):
        return jsonify({"erro": "É preciso aceitar a Política de Privacidade para criar sua conta."}), 400

    try:
        user = UserModel.create(
            name=payload.get("name"),
            email=payload.get("email"),
            password=payload.get("password"),
            phone=payload.get("phone"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    session.permanent = True
    session["user_id"] = user["id"]

    # Endereço é opcional no cadastro — se a pessoa já preencheu, salvamos
    # de uma vez; senão, ela cadastra depois, na etapa de entrega.
    address_payload = payload.get("address")
    if address_payload:
        try:
            AddressModel.create(
                user_id=user["id"],
                label=address_payload.get("label") or "Principal",
                street=address_payload.get("street"),
                number=address_payload.get("number"),
                complement=address_payload.get("complement"),
                neighborhood=address_payload.get("neighborhood"),
                city=address_payload.get("city"),
                state=address_payload.get("state"),
                zip_code=address_payload.get("zip_code"),
                is_default=True,
            )
        except ValueError:
            # Não bloqueia a criação da conta por causa do endereço —
            # a pessoa pode cadastrar um endereço válido depois.
            pass

    return jsonify(user), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("8 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    user = UserModel.authenticate(payload.get("email"), payload.get("password"))

    if user is None:
        return jsonify({"erro": "E-mail ou senha incorretos."}), 401

    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(user)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Não autenticado."}), 401

    user = UserModel.get_by_id(user_id)
    if user is None:
        session.clear()
        return jsonify({"erro": "Não autenticado."}), 401

    return jsonify(user)


@auth_bp.route("/me", methods=["DELETE"])
def delete_me():
    """Exclusão de conta a pedido do titular (direito da LGPD)."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Não autenticado."}), 401

    UserModel.delete_account(user_id)
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    """
    Gera um link de redefinição de senha.

    IMPORTANTE: como este projeto não tem um serviço de e-mail
    configurado, o link é devolvido diretamente aqui e mostrado na
    tela — num sistema real, isso nunca aconteceria: o link sempre
    iria só por e-mail, e esta resposta seria genérica independente de
    o e-mail existir ou não (para não revelar quais e-mails têm
    conta). Deixamos isso bem explícito na interface também.
    """
    payload = request.get_json(silent=True) or {}
    user = UserModel.get_by_email(payload.get("email"))

    if user is None:
        # Mensagem genérica de propósito — não revela se o e-mail existe.
        return jsonify({"erro": "Se esse e-mail existir na nossa base, o link apareceria aqui."}), 404

    token = PasswordResetModel.create_token(user["id"])
    return jsonify({"reset_token": token})


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    payload = request.get_json(silent=True) or {}
    token_row = PasswordResetModel.get_valid_token(payload.get("token"))

    if token_row is None:
        return jsonify({"erro": "Link inválido ou expirado. Peça um novo."}), 400

    try:
        UserModel.update_password(token_row["user_id"], payload.get("new_password"))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    PasswordResetModel.mark_used(payload.get("token"))
    return jsonify({"ok": True})
