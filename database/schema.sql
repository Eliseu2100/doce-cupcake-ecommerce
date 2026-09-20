-- Schema do banco de dados da Doce Cupcake
-- Camada Model: estrutura das tabelas usadas pela aplicação.

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL,
    name          TEXT NOT NULL,
    description   TEXT,
    price         REAL NOT NULL,
    icon          TEXT,
    featured      INTEGER DEFAULT 0,
    rating        REAL DEFAULT 5.0,
    review_count  INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

-- Tamanhos opcionais (P/M/G) com preço próprio, usados pelo produto em destaque
CREATE TABLE IF NOT EXISTS product_sizes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    label      TEXT NOT NULL,
    price      REAL NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Usuários (cadastro / login)
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    phone         TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

-- Endereços salvos pelo usuário (pode ter mais de um: casa, trabalho etc.)
CREATE TABLE IF NOT EXISTS addresses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    label        TEXT NOT NULL,
    street       TEXT NOT NULL,
    number       TEXT NOT NULL,
    complement   TEXT,
    neighborhood TEXT NOT NULL,
    city         TEXT NOT NULL,
    state        TEXT NOT NULL,
    zip_code     TEXT NOT NULL,
    is_default   INTEGER DEFAULT 0,
    created_at   TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS orders (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER,
    created_at            TEXT NOT NULL,
    status                TEXT DEFAULT 'pendente',
    total                 REAL NOT NULL,
    coupon_code           TEXT,
    discount_amount       REAL DEFAULT 0,
    contact_phone         TEXT,
    address_id            INTEGER,
    -- "fotografia" do endereço no momento do pedido: se o cliente editar ou
    -- apagar o endereço salvo depois, o pedido continua com o endereço
    -- correto de quando foi feito.
    delivery_label        TEXT,
    delivery_street       TEXT,
    delivery_number       TEXT,
    delivery_complement   TEXT,
    delivery_neighborhood TEXT,
    delivery_city         TEXT,
    delivery_state        TEXT,
    delivery_zip_code     TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (address_id) REFERENCES addresses (id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    size_label  TEXT,
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    subtotal    REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Cartões salvos (nunca o número completo nem o CVV — só o suficiente
-- para exibir e reconhecer o cartão numa próxima compra).
CREATE TABLE IF NOT EXISTS cards (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    brand      TEXT NOT NULL,
    last4      TEXT NOT NULL,
    card_name  TEXT NOT NULL,
    expiry     TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Pagamentos: modela o "processamento" da área de pagamento.
-- É um pagamento SIMULADO (não há integração com nenhuma operadora real) —
-- guardamos só os 4 últimos dígitos do cartão, nunca o número completo.
CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    method          TEXT NOT NULL,
    card_last4      TEXT,
    card_brand      TEXT,
    installments    INTEGER DEFAULT 1,
    pix_copia_cola  TEXT,
    boleto_barcode  TEXT,
    boleto_due_date TEXT,
    amount          REAL NOT NULL,
    status          TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id)
);

-- Cupons de desconto. Cada inscrição na newsletter gera um cupom de
-- uso único (é a promessa "ganhe 10% no primeiro pedido" — agora com
-- lógica de verdade por trás, e não só o texto na tela).
CREATE TABLE IF NOT EXISTS coupons (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT UNIQUE NOT NULL,
    discount_percent REAL NOT NULL,
    email            TEXT,
    used             INTEGER DEFAULT 0,
    used_by_order_id INTEGER,
    created_at       TEXT NOT NULL
);

-- Tokens de redefinição de senha ("esqueci minha senha"). Como o
-- projeto não tem um serviço de e-mail configurado, o link de
-- redefinição é mostrado na própria tela (deixamos isso bem avisado
-- na interface) — mas o mecanismo (token com validade, uso único,
-- senha só troca com token válido) é o mesmo de um sistema real.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    token      TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    used       INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Lista de e-mails para newsletter (captação de leads, ver apostila de marketing)
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
