"""
Configuração da aplicação.

IMPORTANTE (segurança): DEBUG nunca deve ser True em produção. O modo
debug do Flask expõe um console Python interativo no navegador quando
algo dá erro — isso permite a QUALQUER visitante executar código no
seu servidor. Por isso o valor padrão aqui é sempre "desligado", e só
liga se você explicitamente definir FLASK_DEBUG=1 no ambiente local.
"""
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_PRODUCTION = os.environ.get("RENDER") is not None or os.environ.get("FLASK_ENV") == "production"


class Config:
    """Configurações da aplicação."""

    # Só ativa DEBUG se alguém explicitamente pedir (desenvolvimento local).
    # Nunca fica True por padrão, mesmo que a variável de ambiente falte.
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1" and not IS_PRODUCTION

    DATABASE_PATH = os.path.join(BASE_DIR, "database", "cupcake.db")
    SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

    # Chave usada para assinar o cookie de sessão (login) e para
    # criptografar dados sensíveis em repouso (ver models/crypto_utils.py).
    # Em produção, SECRET_KEY e APP_ENCRYPTION_KEY devem SEMPRE vir de
    # variável de ambiente — nunca do valor padrão abaixo. Se a variável
    # não existir, geramos uma chave aleatória a cada start só para a
    # aplicação não quebrar em desenvolvimento; isso significa que, sem
    # a variável configurada, todas as sessões são derrubadas (logout
    # geral) a cada reinício, e é exatamente esse "castigo" que deve te
    # lembrar de configurar a variável antes de ir para produção.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # --- Segurança de sessão / cookies ---
    SESSION_COOKIE_HTTPONLY = True       # JavaScript não consegue ler o cookie de sessão
    SESSION_COOKIE_SAMESITE = "Lax"      # mitiga CSRF (o cookie não é enviado em requests de outros sites)
    SESSION_COOKIE_SECURE = IS_PRODUCTION  # só envia o cookie por HTTPS quando em produção
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # sessão expira em 8h de inatividade

    # --- Criptografia de dados sensíveis em repouso ---
    # Ver models/crypto_utils.py — telefone e endereço são criptografados
    # no banco. Assim como SECRET_KEY, em produção isso DEVE vir de uma
    # variável de ambiente (senão os dados antigos ficam ilegíveis após
    # um reinício, pois a chave muda).
    APP_ENCRYPTION_KEY = os.environ.get("APP_ENCRYPTION_KEY")

    # Google Analytics (GA4). Deixe em branco enquanto não tiver uma conta —
    # o script só é inserido na página quando essa variável existe (ver
    # views/templates/partials/seo_head.html). Para gerar a sua:
    # analytics.google.com > Administrador > Criar propriedade > Fluxo de
    # dados da Web > copie o "ID de mensuração" (começa com "G-").
    GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "")
