/**
 * View de "Minha Conta": pedidos, endereços e cartões salvos.
 * Só lê e apaga dados via API — toda validação/checagem de dono
 * continua no back-end (Model + Controller).
 */
function formatPrice(v) {
  return "R$ " + v.toFixed(2).replace(".", ",");
}
function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR") + " às " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

async function init() {
  const meRes = await fetch("/api/auth/me");
  if (!meRes.ok) {
    window.location.href = "/login?next=" + encodeURIComponent("/minha-conta");
    return;
  }
  const me = await meRes.json();
  document.getElementById("accountGreeting").textContent = `Olá, ${me.name}! Aqui você acompanha seus pedidos e gerencia endereços e cartões salvos.`;

  loadOrders();
  loadAddresses();
  loadCards();
}

/* ---------------- Abas ---------------- */
document.querySelectorAll(".account-tabs .tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".account-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".account-panel").forEach((p) => (p.hidden = true));
    document.getElementById(
      "tab" + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)
    ).hidden = false;
  });
});

/* ---------------- Pedidos ---------------- */
async function loadOrders() {
  const listEl = document.getElementById("ordersList");
  const res = await fetch("/api/orders");
  if (!res.ok) {
    listEl.innerHTML = '<p class="loading-msg">Não foi possível carregar seus pedidos.</p>';
    return;
  }
  const orders = await res.json();

  if (orders.length === 0) {
    listEl.innerHTML = '<p class="loading-msg">Você ainda não fez nenhum pedido.</p>';
    return;
  }

  listEl.innerHTML = orders
    .map((order) => {
      const itemsSummary = order.items
        .map((i) => `${i.quantity}x ${escapeHtml(i.product_name)}`)
        .join(", ");
      return `
        <div class="order-card">
          <div class="order-card-head">
            <strong>Pedido #${order.id}</strong>
            <span class="order-status ${order.status}">${order.status}</span>
          </div>
          <p class="order-items-mini">${itemsSummary}</p>
          <div class="order-card-foot">
            <span>${formatDate(order.created_at)}</span>
            <b>${formatPrice(order.total - (order.discount_amount || 0))}</b>
          </div>
        </div>`;
    })
    .join("");
}

/* ---------------- Endereços ---------------- */
async function loadAddresses() {
  const listEl = document.getElementById("accountAddressList");
  const res = await fetch("/api/addresses");
  const addresses = res.ok ? await res.json() : [];

  if (addresses.length === 0) {
    listEl.innerHTML = '<p class="address-empty">Nenhum endereço salvo ainda — você pode adicionar um na próxima compra.</p>';
    return;
  }

  listEl.innerHTML = addresses
    .map(
      (addr) => `
      <div class="address-card" style="cursor:default;">
        <div>
          <div class="address-label">${escapeHtml(addr.label)}${addr.is_default ? " · padrão" : ""}</div>
          <div class="address-text">${escapeHtml(addr.street)}, ${escapeHtml(addr.number)}${addr.complement ? " - " + escapeHtml(addr.complement) : ""} — ${escapeHtml(addr.neighborhood)}, ${escapeHtml(addr.city)}/${escapeHtml(addr.state)} — CEP ${escapeHtml(addr.zip_code)}</div>
        </div>
        <div class="card-actions">
          <button class="remove-item-btn" data-id="${addr.id}">Remover</button>
        </div>
      </div>`
    )
    .join("");

  listEl.querySelectorAll(".remove-item-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await fetch(`/api/addresses/${btn.dataset.id}`, { method: "DELETE" });
      showToast("Endereço removido.");
      loadAddresses();
    });
  });
}

/* ---------------- Cartões ---------------- */
async function loadCards() {
  const listEl = document.getElementById("accountCardList");
  const res = await fetch("/api/cards");
  const cards = res.ok ? await res.json() : [];

  if (cards.length === 0) {
    listEl.innerHTML = '<p class="address-empty">Nenhum cartão salvo ainda — você pode salvar um na próxima compra.</p>';
    return;
  }

  listEl.innerHTML = cards
    .map(
      (c) => `
      <div class="address-card" style="cursor:default;">
        <div>
          <div class="address-label">${escapeHtml(c.brand.charAt(0).toUpperCase() + c.brand.slice(1))} •••• ${escapeHtml(c.last4)}${c.is_default ? " · padrão" : ""}</div>
          <div class="address-text">${escapeHtml(c.card_name)} — venc. ${escapeHtml(c.expiry)}</div>
        </div>
        <div class="card-actions">
          <button class="remove-item-btn" data-id="${c.id}">Remover</button>
        </div>
      </div>`
    )
    .join("");

  listEl.querySelectorAll(".remove-item-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await fetch(`/api/cards/${btn.dataset.id}`, { method: "DELETE" });
      showToast("Cartão removido.");
      loadCards();
    });
  });
}

/* ---------------- Excluir conta ---------------- */
document.getElementById("deleteAccountBtn").addEventListener("click", async () => {
  const sure = confirm("Tem certeza que quer excluir sua conta? Essa ação não pode ser desfeita.");
  if (!sure) return;

  const res = await fetch("/api/auth/me", { method: "DELETE" });
  if (res.ok) {
    window.location.href = "/";
  } else {
    showToast("Não foi possível excluir a conta agora.", "error");
  }
});

init();
