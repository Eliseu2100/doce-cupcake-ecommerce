/**
 * View da etapa de entrega.
 * 1) Confirma login (senão, manda para /login).
 * 2) Lista os endereços salvos do usuário (GET /api/addresses).
 * 3) Permite cadastrar um novo endereço (POST /api/addresses).
 * 4) Ao continuar, guarda a escolha (endereço + telefone) para a
 *    página de pagamento usar na hora de criar o pedido.
 */
const CART_KEY = "doce_cupcake_cart";
const DELIVERY_KEY = "doce_cupcake_delivery";

function formatPrice(v) {
  return "R$ " + v.toFixed(2).replace(".", ",");
}
function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (e) {
    return [];
  }
}

let cart = [];
let addresses = [];
let selectedAddressId = null;

const loadingEl = document.getElementById("entregaLoading");
const contentEl = document.getElementById("entregaContent");
const addressListEl = document.getElementById("addressList");
const summaryItemsEl = document.getElementById("summaryItems");
const summaryTotalEl = document.getElementById("summaryTotal");
const contactPhoneInput = document.getElementById("contactPhone");
const entregaError = document.getElementById("entregaError");

async function init() {
  cart = getCart();
  if (cart.length === 0) {
    window.location.href = "/#cardapio";
    return;
  }

  const meRes = await fetch("/api/auth/me");
  if (!meRes.ok) {
    window.location.href = "/login?next=" + encodeURIComponent("/entrega");
    return;
  }
  const me = await meRes.json();
  if (me.phone) {
    contactPhoneInput.value = me.phone;
  }

  await loadAddresses();
  renderSummary();

  loadingEl.hidden = true;
  contentEl.hidden = false;
}

async function loadAddresses() {
  const res = await fetch("/api/addresses");
  addresses = res.ok ? await res.json() : [];
  renderAddresses();
}

function renderAddresses() {
  if (addresses.length === 0) {
    addressListEl.innerHTML = '<p class="address-empty">Você ainda não tem endereços salvos. Adicione um abaixo.</p>';
    selectedAddressId = null;
    return;
  }

  addressListEl.innerHTML = addresses
    .map(
      (addr) => `
      <label class="address-card ${addr.id === selectedAddressId ? "selected" : ""}" data-id="${addr.id}">
        <input type="radio" name="address" value="${addr.id}" ${addr.id === selectedAddressId ? "checked" : ""}>
        <div>
          <div class="address-label">${escapeHtml(addr.label)}${addr.is_default ? " · padrão" : ""}</div>
          <div class="address-text">${escapeHtml(addr.street)}, ${escapeHtml(addr.number)}${addr.complement ? " - " + escapeHtml(addr.complement) : ""} — ${escapeHtml(addr.neighborhood)}, ${escapeHtml(addr.city)}/${escapeHtml(addr.state)} — CEP ${escapeHtml(addr.zip_code)}</div>
        </div>
      </label>`
    )
    .join("");

  if (selectedAddressId === null) {
    const defaultAddr = addresses.find((a) => a.is_default) || addresses[0];
    selectedAddressId = defaultAddr.id;
    renderAddresses();
    return;
  }

  addressListEl.querySelectorAll(".address-card").forEach((card) => {
    card.addEventListener("click", () => {
      selectedAddressId = Number(card.dataset.id);
      renderAddresses();
    });
  });
}

function renderSummary() {
  let total = 0;
  summaryItemsEl.innerHTML = cart
    .map((item) => {
      const subtotal = item.unit_price * item.quantity;
      total += subtotal;
      return `
        <div class="summary-line">
          <span>${escapeHtml(item.name)}${item.size ? " (" + escapeHtml(item.size) + ")" : ""}
            <small>${item.quantity}x ${formatPrice(item.unit_price)}</small>
          </span>
          <span>${formatPrice(subtotal)}</span>
        </div>`;
    })
    .join("");
  summaryTotalEl.textContent = formatPrice(total);
}

/* ---------------- Novo endereço ---------------- */
const showNewAddressBtn = document.getElementById("showNewAddressBtn");
const newAddressForm = document.getElementById("newAddressForm");

showNewAddressBtn.addEventListener("click", () => {
  newAddressForm.hidden = !newAddressForm.hidden;
});

setupCepAutocomplete({
  zipId: "zipCode",
  streetId: "street",
  neighborhoodId: "neighborhood",
  cityId: "city",
  stateId: "state",
  feedbackId: "cepFeedback",
});

newAddressForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("addressError");
  errorEl.textContent = "";

  const payload = {
    label: document.getElementById("label").value,
    zip_code: document.getElementById("zipCode").value,
    street: document.getElementById("street").value,
    number: document.getElementById("number").value,
    complement: document.getElementById("complement").value,
    neighborhood: document.getElementById("neighborhood").value,
    city: document.getElementById("city").value,
    state: document.getElementById("state").value,
  };

  try {
    const res = await fetch("/api/addresses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.erro || "Não foi possível salvar o endereço.";
      return;
    }

    addresses.push(data);
    selectedAddressId = data.id;
    renderAddresses();
    newAddressForm.reset();
    newAddressForm.hidden = true;
    showToast("Endereço salvo!");
  } catch (err) {
    errorEl.textContent = "Erro de conexão com o servidor.";
  }
});

/* ---------------- Continuar para pagamento ---------------- */
document.getElementById("continueBtn").addEventListener("click", () => {
  entregaError.textContent = "";

  if (!selectedAddressId) {
    entregaError.textContent = "Selecione ou cadastre um endereço de entrega.";
    return;
  }

  const phoneDigits = contactPhoneInput.value.replace(/\D/g, "");
  if (phoneDigits.length < 10 || phoneDigits.length > 11) {
    entregaError.textContent = "Informe um telefone de contato válido (com DDD).";
    return;
  }

  const selectedAddress = addresses.find((a) => a.id === selectedAddressId);

  localStorage.setItem(
    DELIVERY_KEY,
    JSON.stringify({
      address_id: selectedAddressId,
      contact_phone: phoneDigits,
      address_label: selectedAddress ? selectedAddress.label : "",
      address_text: selectedAddress
        ? `${selectedAddress.street}, ${selectedAddress.number} — ${selectedAddress.neighborhood}, ${selectedAddress.city}/${selectedAddress.state}`
        : "",
    })
  );
  window.location.href = "/pagamento";
});

init();
