/**
 * View (front-end): responsável apenas por pedir dados ao back-end
 * (Controller -> Model) via fetch() e por exibir o resultado na tela.
 * Nenhuma regra de preço é calculada aqui — o total do pedido é
 * sempre recalculado no servidor, em models/order_model.py.
 */

const ICONS = {
  donut: "🍩",
  cookie: "🍪",
  cupcake_cherry: "🧁",
  brownie: "🍫",
  cake_choc: "🎂",
  pie_strawberry: "🍰",
  pie_lemon: "🍋",
  icecream: "🍨",
};

const CART_KEY = "doce_cupcake_cart";

const state = {
  products: [],
  categories: [],
  cart: [], // { product_id, name, size, quantity, unit_price }
};

function loadCartFromStorage() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveCartToStorage() {
  localStorage.setItem(CART_KEY, JSON.stringify(state.cart));
}

function formatPrice(v) {
  return "R$ " + v.toFixed(2).replace(".", ",");
}

function scrollToId(id) {
  document.getElementById(id).scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------------- Header / menu mobile ---------------- */
const header = document.getElementById("siteHeader");
window.addEventListener("scroll", () => {
  header.classList.toggle("scrolled", window.scrollY > 30);
});

const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
menuToggle.addEventListener("click", () => {
  const isOpen = navLinks.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", isOpen);
});
navLinks.querySelectorAll("a").forEach((a) =>
  a.addEventListener("click", () => {
    navLinks.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
  })
);

/* ---------------- Carrinho (UI) ---------------- */
const cartPanel = document.getElementById("cartPanel");
const cartOverlay = document.getElementById("cartOverlay");
const cartToggle = document.getElementById("cartToggle");
const cartClose = document.getElementById("cartClose");
const cartItemsEl = document.getElementById("cartItems");
const cartTotalEl = document.getElementById("cartTotal");
const cartCountEl = document.getElementById("cartCount");
const cartFeedback = document.getElementById("cartFeedback");
const checkoutBtn = document.getElementById("checkoutBtn");

function openCart() {
  cartPanel.classList.add("open");
  cartOverlay.classList.add("open");
  cartPanel.setAttribute("aria-hidden", "false");
}
function closeCart() {
  cartPanel.classList.remove("open");
  cartOverlay.classList.remove("open");
  cartPanel.setAttribute("aria-hidden", "true");
}
cartToggle.addEventListener("click", openCart);
cartClose.addEventListener("click", closeCart);
cartOverlay.addEventListener("click", closeCart);

function addToCart(item) {
  // Junta itens iguais (mesmo produto + mesmo tamanho)
  const existing = state.cart.find(
    (i) => i.product_id === item.product_id && i.size === item.size
  );
  if (existing) {
    existing.quantity += item.quantity;
  } else {
    state.cart.push(item);
  }
  saveCartToStorage();
  renderCart();
  openCart();
  bumpCartIcon();
  showToast(`${item.name} adicionado ao carrinho`);
}

function bumpCartIcon() {
  cartToggle.classList.remove("cart-bump");
  // força o navegador a "esquecer" a animação anterior antes de reaplicar
  void cartToggle.offsetWidth;
  cartToggle.classList.add("cart-bump");
}

function removeFromCart(index) {
  state.cart.splice(index, 1);
  saveCartToStorage();
  renderCart();
}

function renderCart() {
  cartCountEl.textContent = `(${state.cart.reduce((sum, i) => sum + i.quantity, 0)})`;

  if (state.cart.length === 0) {
    cartItemsEl.innerHTML = '<p class="cart-empty">Seu carrinho está vazio.</p>';
    cartTotalEl.textContent = formatPrice(0);
    return;
  }

  let total = 0;
  cartItemsEl.innerHTML = state.cart
    .map((item, index) => {
      const subtotal = item.unit_price * item.quantity;
      total += subtotal;
      return `
        <div class="cart-line">
          <div>
            <div class="cart-line-name">${escapeHtml(item.name)}${item.size ? " (" + escapeHtml(item.size) + ")" : ""}</div>
            <div class="cart-line-meta">${item.quantity}x ${formatPrice(item.unit_price)}</div>
          </div>
          <div style="text-align:right;">
            <div>${formatPrice(subtotal)}</div>
            <button class="cart-line-remove" data-index="${index}">remover</button>
          </div>
        </div>`;
    })
    .join("");

  cartTotalEl.textContent = formatPrice(total);

  cartItemsEl.querySelectorAll(".cart-line-remove").forEach((btn) => {
    btn.addEventListener("click", () => removeFromCart(Number(btn.dataset.index)));
  });
}

checkoutBtn.addEventListener("click", () => {
  if (state.cart.length === 0) {
    cartFeedback.textContent = "Adicione algo ao carrinho antes de finalizar.";
    return;
  }
  saveCartToStorage();
  window.location.href = "/entrega";
});

/* ---------------- Cardápio (GET /api/categories, /api/products) ---------------- */
const tabsEl = document.getElementById("tabs");
const menuListEl = document.getElementById("menuList");

async function loadCategories() {
  const res = await fetch("/api/categories");
  state.categories = await res.json();

  state.categories.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "tab-btn";
    btn.dataset.cat = cat.slug;
    btn.textContent = cat.name;
    tabsEl.appendChild(btn);
  });

  tabsEl.querySelectorAll(".tab-btn").forEach((tab) => {
    tab.addEventListener("click", () => {
      tabsEl.querySelectorAll(".tab-btn").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      loadProducts(tab.dataset.cat);
    });
  });
}

async function loadProducts(categorySlug) {
  menuListEl.innerHTML = Array.from({ length: 4 })
    .map(() => '<div class="skeleton skeleton-menu-item"></div>')
    .join("");

  const url = categorySlug && categorySlug !== "todos"
    ? `/api/products?category=${encodeURIComponent(categorySlug)}`
    : "/api/products";

  const res = await fetch(url);
  const products = await res.json();
  state.products = products;

  if (products.length === 0) {
    menuListEl.innerHTML = '<p class="loading-msg">Nenhum item nessa categoria ainda.</p>';
    return;
  }

  menuListEl.classList.remove("fade-in");
  menuListEl.innerHTML = products
    .map(
      (p) => `
      <div class="menu-item">
        <div class="icon-box">${ICONS[p.icon] || "🍰"}</div>
        <div class="item-info">
          <h4>${escapeHtml(p.name)}</h4>
          <p>${escapeHtml(p.description || "")}</p>
        </div>
        <div class="item-side">
          <span class="price">${formatPrice(p.price)}</span>
          <button class="add-btn" data-id="${p.id}" data-name="${escapeHtml(p.name)}" data-price="${p.price}" aria-label="Adicionar ${escapeHtml(p.name)}">+</button>
        </div>
      </div>`
    )
    .join("");
  void menuListEl.offsetWidth;
  menuListEl.classList.add("fade-in");

  menuListEl.querySelectorAll(".add-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      addToCart({
        product_id: Number(btn.dataset.id),
        name: btn.dataset.name,
        size: null,
        quantity: 1,
        unit_price: Number(btn.dataset.price),
      });
    });
  });
}

/* ---------------- Produto em destaque (GET /api/products/featured) ---------------- */
const spotlightEl = document.getElementById("spotlight");

async function loadFeaturedProduct() {
  spotlightEl.innerHTML = '<div class="skeleton skeleton-spotlight" style="grid-column:1/-1;"></div>';

  const res = await fetch("/api/products/featured");
  if (!res.ok) {
    spotlightEl.innerHTML = '<p class="loading-msg" style="color:#fff;">Nenhum destaque no momento.</p>';
    return;
  }
  const product = await res.json();
  renderSpotlight(product);
}

function renderSpotlight(product) {
  const stars = "★★★★★";
  const sizesHtml = product.sizes
    .map(
      (s, i) => `<button class="size-chip ${i === 0 ? "active" : ""}" data-label="${s.label}" data-price="${s.price}">${s.label}</button>`
    )
    .join("");

  spotlightEl.innerHTML = `
    <div class="spotlight-art">
      <svg viewBox="0 0 300 320" fill="none">
        <path d="M70 150 L230 150 L212 290 Q209 306 193 306 L107 306 Q91 306 88 290 Z" fill="#FBEBD3"/>
        <path d="M60 150 C40 110 60 70 100 55 C120 47 130 30 150 30 C170 30 180 47 200 55 C240 70 260 110 240 150 C230 168 210 172 195 156 C182 142 170 118 150 118 C130 118 118 142 105 156 C90 172 70 168 60 150 Z" fill="#D6336C"/>
        <circle cx="150" cy="42" r="13" fill="#9C1F52"/>
        <circle cx="112" cy="96" r="5" fill="#6FC3A9"/>
        <circle cx="190" cy="88" r="4" fill="#F4B740"/>
        <circle cx="170" cy="70" r="4" fill="#fff"/>
        <circle cx="128" cy="70" r="4" fill="#F4B740"/>
      </svg>
    </div>
    <div>
      <span class="eyebrow-chip" style="background:rgba(255,255,255,.1); color:var(--butter);"><span class="dot" style="background:var(--butter)"></span> Destaque da semana</span>
      <h2>${product.name}</h2>
      <div class="rating-line">${stars} ${product.rating.toFixed(1)} · ${product.review_count.toLocaleString("pt-BR")} avaliações</div>
      <p class="desc">${product.description}</p>
      <div class="size-row" id="sizeRow">${sizesHtml}</div>
      <div class="buy-row">
        <div class="qty-stepper">
          <button id="qtyMinus" aria-label="Diminuir quantidade">−</button>
          <span id="qtyValue">1</span>
          <button id="qtyPlus" aria-label="Aumentar quantidade">+</button>
        </div>
        <span class="spotlight-price" id="spotlightPrice">${formatPrice(product.sizes[0].price)}</span>
        <button class="btn btn-butter" id="buyBtn">Adicionar ao carrinho</button>
      </div>
      <p class="buy-feedback" id="buyFeedback"></p>
    </div>`;

  let qty = 1;
  let selectedSize = product.sizes[0].label;
  let unitPrice = product.sizes[0].price;

  const sizeChips = spotlightEl.querySelectorAll(".size-chip");
  const spotlightPriceEl = spotlightEl.querySelector("#spotlightPrice");
  const qtyValueEl = spotlightEl.querySelector("#qtyValue");

  function updatePrice() {
    spotlightPriceEl.textContent = formatPrice(unitPrice * qty);
  }

  sizeChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      sizeChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      selectedSize = chip.dataset.label;
      unitPrice = Number(chip.dataset.price);
      updatePrice();
    });
  });

  spotlightEl.querySelector("#qtyMinus").addEventListener("click", () => {
    if (qty > 1) { qty--; qtyValueEl.textContent = qty; updatePrice(); }
  });
  spotlightEl.querySelector("#qtyPlus").addEventListener("click", () => {
    if (qty < 10) { qty++; qtyValueEl.textContent = qty; updatePrice(); }
  });
  spotlightEl.querySelector("#buyBtn").addEventListener("click", () => {
    addToCart({
      product_id: product.id,
      name: product.name,
      size: selectedSize,
      quantity: qty,
      unit_price: unitPrice,
    });
    spotlightEl.querySelector("#buyFeedback").textContent = "Adicionado ao carrinho!";
  });
}

/* ---------------- Inicialização ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  state.cart = loadCartFromStorage();
  loadCategories();
  loadProducts("todos");
  loadFeaturedProduct();
  renderCart();
});
