"""
Ponto de entrada da aplicação.

Aqui a aplicação é "montada": registramos os Controllers (Blueprints),
inicializamos o banco de dados (camada Model) e apontamos onde ficam
as Views (templates HTML e arquivos estáticos de CSS/JS).
"""
from flask import Flask, render_template
from config import Config
from extensions import limiter
from models.database import init_db, close_db
from controllers.main_controller import main_bp
from controllers.product_controller import product_bp
from controllers.order_controller import order_bp
from controllers.auth_controller import auth_bp
from controllers.address_controller import address_bp
from controllers.card_controller import card_bp
from controllers.cep_controller import cep_bp
from controllers.payment_controller import payment_bp
from controllers.coupon_controller import coupon_bp
from controllers.newsletter_controller import newsletter_bp


def create_app():
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="views/static",
    )
    app.config.from_object(Config)

    # Rate limiting (proteção contra força bruta / abuso da API)
    limiter.init_app(app)

    # Inicializa o banco (cria as tabelas e popula dados de exemplo, se necessário)
    with app.app_context():
        init_db(app)

    # Fecha a conexão com o banco ao final de cada requisição
    app.teardown_appcontext(close_db)

    # Registra os Controllers da aplicação
    app.register_blueprint(main_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(address_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(cep_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(coupon_bp)
    app.register_blueprint(newsletter_bp)

    @app.context_processor
    def inject_globals():
        """Disponibiliza essas variáveis em TODOS os templates, sem
        precisar repetir em cada rota do main_controller."""
        return {"ga_measurement_id": app.config.get("GA_MEASUREMENT_ID", "")}

    @app.after_request
    def set_security_headers(response):
        """Cabeçalhos HTTP de segurança recomendados pela OWASP para
        qualquer aplicação web voltada ao público."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Se o Google Analytics estiver configurado (GA_MEASUREMENT_ID),
        # liberamos os domínios do próprio Google Analytics na CSP —
        # senão o navegador bloqueia o script por segurança.
        ga_hosts = " https://www.googletagmanager.com https://www.google-analytics.com" if app.config.get("GA_MEASUREMENT_ID") else ""
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            f"script-src 'self' 'unsafe-inline'{ga_hosts}; "
            "img-src 'self' data:" + (" https://www.google-analytics.com" if ga_hosts else "") + "; "
            f"connect-src 'self'{ga_hosts}"
        )
        if not app.config["DEBUG"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        # Nunca mostra o stack trace pro visitante, mesmo se DEBUG
        # acabar ligado por engano — só uma página amigável.
        return render_template("404.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    # DEBUG vem de Config (nunca True por padrão — ver config.py)
    app.run(debug=app.config["DEBUG"], port=5000)
