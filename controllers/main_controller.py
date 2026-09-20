"""
Camada Controller — páginas HTML da aplicação (as "telas").

Cada rota passa para o template um pequeno dicionário de SEO
(meta_title, meta_description, robots) — assim cada página tem título
e descrição únicos, uma das recomendações centrais do guia de SEO
On-Page (evitar titles/descriptions duplicadas ou ausentes).
"""
from flask import Blueprint, render_template, session, Response, url_for
from models.user_model import UserModel
from models.product_model import ProductModel

main_bp = Blueprint("main", __name__)

SITE_NAME = "Doce Cupcake"


def _current_user():
    """Busca o usuário logado (se houver) para exibir na navegação."""
    user_id = session.get("user_id")
    return UserModel.get_by_id(user_id) if user_id else None


@main_bp.route("/")
def home():
    seo = {
        "title": "Doce Cupcake — Ateliê de doces artesanais | Cupcakes, bolos e tortas",
        "description": "Cupcakes, bolos, tortas e sorvetes artesanais feitos à mão todos os "
                        "dias. Peça online e receba em casa em até 40 minutos.",
        "robots": "index, follow",
    }
    return render_template(
        "index.html",
        seo=seo,
        site_name=SITE_NAME,
        user=_current_user(),
        # Lista de produtos renderizada no HTML (não só via JavaScript),
        # para o schema.org de cada produto (ver index.html) já vir
        # pronto na primeira resposta do servidor — o Google não
        # depende de rodar JavaScript para ver isso.
        products_for_schema=ProductModel.get_all(),
    )


@main_bp.route("/login")
def login_page():
    seo = {
        "title": f"Entrar na sua conta — {SITE_NAME}",
        "description": "Acesse sua conta Doce Cupcake para acompanhar pedidos e finalizar compras.",
        "robots": "noindex, nofollow",
    }
    return render_template("login.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/cadastro")
def cadastro_page():
    seo = {
        "title": f"Criar conta — {SITE_NAME}",
        "description": "Crie sua conta gratuita na Doce Cupcake e faça seu primeiro pedido.",
        "robots": "noindex, nofollow",
    }
    return render_template("cadastro.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/entrega")
def entrega_page():
    seo = {
        "title": f"Endereço de entrega — {SITE_NAME}",
        "description": "Selecione o endereço de entrega e o telefone de contato do seu pedido.",
        "robots": "noindex, nofollow",
    }
    return render_template("entrega.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/pagamento")
def pagamento_page():
    seo = {
        "title": f"Pagamento — {SITE_NAME}",
        "description": "Finalize o pagamento do seu pedido na Doce Cupcake.",
        "robots": "noindex, nofollow",
    }
    return render_template("pagamento.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/esqueci-senha")
def esqueci_senha_page():
    seo = {
        "title": f"Recuperar senha — {SITE_NAME}",
        "description": "Recupere o acesso à sua conta Doce Cupcake.",
        "robots": "noindex, nofollow",
    }
    return render_template("esqueci-senha.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/redefinir-senha")
def redefinir_senha_page():
    seo = {
        "title": f"Criar nova senha — {SITE_NAME}",
        "description": "Defina uma nova senha para sua conta Doce Cupcake.",
        "robots": "noindex, nofollow",
    }
    return render_template("redefinir-senha.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/minha-conta")
def minha_conta_page():
    seo = {
        "title": f"Minha conta — {SITE_NAME}",
        "description": "Seus pedidos, endereços e cartões salvos.",
        "robots": "noindex, nofollow",
    }
    return render_template("minha-conta.html", seo=seo, site_name=SITE_NAME, user=_current_user())


@main_bp.route("/privacidade")
def privacidade_page():
    seo = {
        "title": f"Política de Privacidade — {SITE_NAME}",
        "description": "Como a Doce Cupcake coleta, usa e protege seus dados pessoais.",
        "robots": "index, follow",
    }
    return render_template("privacidade.html", seo=seo, site_name=SITE_NAME)


@main_bp.route("/robots.txt")
def robots():
    """
    Bloqueia a indexação de páginas transacionais (login, cadastro,
    pagamento e a própria API) — só a página inicial deve aparecer nos
    buscadores. Recomendação do guia de SEO Técnico.
    """
    lines = [
        "User-agent: *",
        "Disallow: /login",
        "Disallow: /cadastro",
        "Disallow: /entrega",
        "Disallow: /pagamento",
        "Disallow: /esqueci-senha",
        "Disallow: /redefinir-senha",
        "Disallow: /minha-conta",
        "Disallow: /api/",
        "Allow: /$",
        f"Sitemap: {url_for('main.sitemap', _external=True)}",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap():
    """Sitemap simples com a única página pública indexável do site."""
    home_url = url_for("main.home", _external=True)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{home_url}</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")
