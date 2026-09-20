/**
 * View da página de pagamento.
 * 1) Lê o carrinho e a entrega (endereço/telefone) salvos no localStorage.
 * 2) Confirma que o usuário está logado.
 * 3) Cria o pedido (POST /api/orders) e processa o pagamento
 *    (POST /api/orders/<id>/pagamento) — toda a validação de cartão,
 *    cálculo de parcelas, geração de Pix/boleto acontece no back-end.
 */
const CART_KEY = "doce_cupcake_cart";
const DELIVERY_KEY = "doce_cupcake_delivery";

function formatPrice(v) {
  return "R$ " + v.toFixed(2).replace(".", ",");
}
function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch (e) { return []; }
}
function getDelivery() {
  try { return JSON.parse(localStorage.getItem(DELIVERY_KEY)); } catch (e) { return null; }
}
function clearCart() {
  localStorage.removeItem(CART_KEY);
  localStorage.removeItem(DELIVERY_KEY);
}

/* Detecção de bandeira e Luhn no navegador — só para dar feedback
   imediato enquanto a pessoa digita. A validação que decide de
   verdade acontece no back-end (models/card_service.py). */
function luhnValido(digits) {
  let soma = 0, dobrar = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = parseInt(digits[i], 10);
    if (dobrar) { d *= 2; if (d > 9) d -= 9; }
    soma += d;
    dobrar = !dobrar;
  }
  return soma % 10 === 0;
}
function detectarBandeira(digits) {
  if (/^4/.test(digits)) return { nome: "Visa", cvvLen: 3 };
  if (/^5[1-5]/.test(digits) || /^2(2[2-9]|[3-6]\d|7[01]|720)/.test(digits)) return { nome: "Mastercard", cvvLen: 3 };
  if (/^3[47]/.test(digits)) return { nome: "Amex", cvvLen: 4 };
  if (/^(4011|4312|4389|4514|4573|6277|6362|6363|650|6516|6550)/.test(digits)) return { nome: "Elo", cvvLen: 3 };
  return null;
}
function calcularParcelasPreview(total, parcelas) {
  if (parcelas <= 3) return { valorParcela: total / parcelas, totalComJuros: total };
  const taxa = 0.0199;
  const totalComJuros = total * Math.pow(1 + taxa, parcelas);
  return { valorParcela: totalComJuros / parcelas, totalComJuros };
}

let cart = [];
let cartTotal = 0;
let discountPercent = 0;
let appliedCouponCode = null;
let delivery = null;
let savedCards = [];
let selectedCardId = null;

const loadingEl = document.getElementById("paymentLoading");
const contentEl = document.getElementById("paymentContent");
const successEl = document.getElementById("paymentSuccess");
const summaryItemsEl = document.getElementById("summaryItems");
const summaryTotalEl = document.getElementById("summaryTotal");

async function init() {
  cart = getCart();
  delivery = getDelivery();

  if (cart.length === 0) { window.location.href = "/#cardapio"; return; }

  const meRes = await fetch("/api/auth/me");
  if (!meRes.ok) { window.location.href = "/login?next=" + encodeURIComponent("/pagamento"); return; }

  if (!delivery || !delivery.address_id || !delivery.contact_phone) {
    window.location.href = "/entrega";
    return;
  }

  await loadSavedCards();
  renderSummary();
  loadingEl.hidden = true;
  contentEl.hidden = false;
}

function renderSummary() {
  const deliveryEl = document.getElementById("deliverySummary");
  if (deliveryEl && delivery) {
    deliveryEl.innerHTML = `
      <div class="delivery-summary-box">
        <strong>${escapeHtml(delivery.address_label || "Endereço")}</strong>
        <p>${escapeHtml(delivery.address_text || "")}</p>
        <p>📞 ${escapeHtml(delivery.contact_phone)}</p>
        <a href="/entrega">Trocar endereço</a>
      </div>`;
  }

  cartTotal = 0;
  summaryItemsEl.innerHTML = cart.map((item) => {
    const subtotal = item.unit_price * item.quantity;
    cartTotal += subtotal;
    return `
      <div class="summary-line">
        <span>${item.name}${item.size ? " (" + item.size + ")" : ""}
          <small>${item.quantity}x ${formatPrice(item.unit_price)}</small>
        </span>
        <span>${formatPrice(subtotal)}</span>
      </div>`;
  }).join("");
  updateTotals();
}

function updateTotals() {
  const discountAmount = round2(cartTotal * (discountPercent / 100));
  const payable = round2(cartTotal - discountAmount);

  const discountRow = document.getElementById("summaryDiscountRow");
  if (discountPercent > 0) {
    discountRow.hidden = false;
    document.getElementById("summaryDiscount").textContent = "- " + formatPrice(discountAmount);
  } else {
    discountRow.hidden = true;
  }

  summaryTotalEl.textContent = formatPrice(payable);
  updateInstallmentsPreview(payable);
}
function round2(v) { return Math.round(v * 100) / 100; }

/* ---------------- Cartões salvos ---------------- */
const savedCardsListEl = document.getElementById("savedCardsList");
const useNewCardBtn = document.getElementById("useNewCardBtn");
const cardForm = document.getElementById("cardForm");
const savedCardForm = document.getElementById("savedCardForm");

async function loadSavedCards() {
  const res = await fetch("/api/cards");
  savedCards = res.ok ? await res.json() : [];
  if (savedCards.length > 0) {
    selectedCardId = savedCards.find((c) => c.is_default)?.id || savedCards[0].id;
    renderSavedCards();
    showSavedCardFlow();
  }
}

function renderSavedCards() {
  savedCardsListEl.hidden = false;
  useNewCardBtn.hidden = false;
  savedCardsListEl.innerHTML = savedCards.map((c) => `
    <label class="address-card ${c.id === selectedCardId ? "selected" : ""}" data-id="${c.id}">
      <input type="radio" name="savedCard" value="${c.id}" ${c.id === selectedCardId ? "checked" : ""}>
      <div>
        <div class="address-label">${c.brand.charAt(0).toUpperCase() + c.brand.slice(1)} •••• ${c.last4}${c.is_default ? " · padrão" : ""}</div>
        <div class="address-text">${escapeHtml(c.card_name)} — venc. ${escapeHtml(c.expiry)}</div>
      </div>
    </label>`).join("");

  savedCardsListEl.querySelectorAll(".address-card").forEach((card) => {
    card.addEventListener("click", () => {
      selectedCardId = Number(card.dataset.id);
      renderSavedCards();
      document.getElementById("savedCardLabel").textContent =
        `Confirmar pagamento com o cartão terminado em ${savedCards.find(c => c.id === selectedCardId).last4}`;
    });
  });

  document.getElementById("savedCardLabel").textContent =
    `Confirmar pagamento com o cartão terminado em ${savedCards.find(c => c.id === selectedCardId)?.last4 || ""}`;
}

function showSavedCardFlow() {
  cardForm.hidden = true;
  savedCardForm.hidden = false;
}
function showNewCardFlow() {
  cardForm.hidden = false;
  savedCardForm.hidden = true;
}

useNewCardBtn.addEventListener("click", () => {
  const usingSaved = !savedCardForm.hidden;
  if (usingSaved) {
    showNewCardFlow();
    useNewCardBtn.textContent = "Usar cartão salvo";
  } else {
    showSavedCardFlow();
    useNewCardBtn.textContent = "Usar outro cartão";
  }
});

/* ---------------- Alternância de método de pagamento ---------------- */
const tabs = document.querySelectorAll(".pay-method-tab");
const cardPanel = document.getElementById("cardPanel");
const pixPanel = document.getElementById("pixPanel");
const boletoPanel = document.getElementById("boletoPanel");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    cardPanel.hidden = tab.dataset.method !== "cartao";
    pixPanel.hidden = tab.dataset.method !== "pix";
    boletoPanel.hidden = tab.dataset.method !== "boleto";
  });
});

/* ---------------- Cartão novo: máscaras + bandeira + parcelas ---------------- */
const cardNumberInput = document.getElementById("cardNumber");
const cardBrandBadge = document.getElementById("cardBrandBadge");

/* ---------------- Cartão virtual (prévia animada) ---------------- */
const virtualCard = document.getElementById("virtualCard");
const virtualCardBrand = document.getElementById("virtualCardBrand");
const virtualCardNumber = document.getElementById("virtualCardNumber");
const virtualCardName = document.getElementById("virtualCardName");
const virtualCardExpiry = document.getElementById("virtualCardExpiry");

let bandeiraAtual = null;

function atualizarCartaoVirtual({ digits, nomeBandeira, nome, validade }) {
  if (digits !== undefined) {
    const grupos = (digits.padEnd(16, "•")).match(/.{1,4}/g) || [];
    virtualCardNumber.textContent = grupos.join(" ");
  }
  if (nome !== undefined) {
    virtualCardName.textContent = nome.trim() ? nome : "SEU NOME AQUI";
  }
  if (validade !== undefined) {
    virtualCardExpiry.textContent = validade || "MM/AA";
  }
  if (nomeBandeira !== bandeiraAtual) {
    bandeiraAtual = nomeBandeira;
    virtualCardBrand.textContent = nomeBandeira || "cartão";
    virtualCard.dataset.brand = nomeBandeira ? nomeBandeira.toLowerCase() : "";
    virtualCard.classList.remove("brand-detected");
    void virtualCard.offsetWidth; // reinicia a animação mesmo se a bandeira "voltar" à mesma
    virtualCard.classList.add("brand-detected");
  }
}

cardNumberInput.addEventListener("input", () => {
  const rawDigits = cardNumberInput.value.replace(/\D/g, "").slice(0, 16);
  cardNumberInput.value = rawDigits.replace(/(.{4})/g, "$1 ").trim();

  let nomeBandeira = null;
  if (rawDigits.length >= 12) {
    const bandeira = detectarBandeira(rawDigits);
    if (bandeira) {
      nomeBandeira = bandeira.nome;
      const ok = luhnValido(rawDigits);
      cardBrandBadge.textContent = bandeira.nome + (ok ? " ✓" : " (verifique o número)");
      cardBrandBadge.className = "card-brand-badge " + (ok ? "brand-ok" : "brand-warn");
    } else {
      cardBrandBadge.textContent = "";
    }
  } else {
    cardBrandBadge.textContent = "";
  }

  atualizarCartaoVirtual({ digits: rawDigits, nomeBandeira });
});

const cardNameInput = document.getElementById("cardName");
cardNameInput.addEventListener("input", () => {
  atualizarCartaoVirtual({ nome: cardNameInput.value });
});

const cardExpiryInput = document.getElementById("cardExpiry");
cardExpiryInput.addEventListener("input", () => {
  let v = cardExpiryInput.value.replace(/\D/g, "").slice(0, 4);
  if (v.length > 2) v = v.slice(0, 2) + "/" + v.slice(2);
  cardExpiryInput.value = v;
  atualizarCartaoVirtual({ validade: v });
});

function updateInstallmentsPreview() {
  const select = document.getElementById("installments");
  if (!select) return;
  const n = parseInt(select.value, 10);
  const discountAmount = round2(cartTotal * (discountPercent / 100));
  const payable = round2(cartTotal - discountAmount);
  const { valorParcela, totalComJuros } = calcularParcelasPreview(payable, n);
  const previewEl = document.getElementById("installmentsPreview");
  if (n === 1) {
    previewEl.textContent = `Total: ${formatPrice(totalComJuros)}`;
  } else {
    previewEl.textContent = `${n}x de ${formatPrice(valorParcela)} (total ${formatPrice(totalComJuros)})`;
  }
}
document.getElementById("installments").addEventListener("change", () => updateInstallmentsPreview());

/* ---------------- Cupom de desconto ---------------- */
const couponInput = document.getElementById("couponInput");
const couponFeedback = document.getElementById("couponFeedback");
const applyCouponBtn = document.getElementById("applyCouponBtn");

applyCouponBtn.addEventListener("click", async () => {
  const code = couponInput.value.trim();
  couponFeedback.textContent = "";
  if (!code) {
    couponFeedback.textContent = "Digite um código de cupom.";
    return;
  }

  applyCouponBtn.disabled = true;
  applyCouponBtn.textContent = "Verificando...";

  try {
    const res = await fetch(`/api/coupons/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (!res.ok) {
      discountPercent = 0;
      appliedCouponCode = null;
      couponFeedback.textContent = data.erro || "Cupom inválido.";
      couponFeedback.className = "coupon-feedback error";
    } else {
      discountPercent = data.discount_percent;
      appliedCouponCode = data.code;
      couponFeedback.textContent = `Cupom aplicado: ${data.discount_percent}% de desconto! 🎉`;
      couponFeedback.className = "coupon-feedback ok";
      couponInput.disabled = true;
    }
  } catch (err) {
    couponFeedback.textContent = "Erro de conexão ao verificar o cupom.";
  } finally {
    applyCouponBtn.disabled = false;
    applyCouponBtn.textContent = "Aplicar";
    updateTotals();
  }
});

/* ---------------- Criação do pedido + pagamento ---------------- */
async function createOrderAndPay(method, extra) {
  const orderPayload = {
    items: cart.map((i) => ({ product_id: i.product_id, size: i.size, quantity: i.quantity })),
    address_id: delivery.address_id,
    contact_phone: delivery.contact_phone,
    coupon_code: appliedCouponCode || null,
  };

  const orderRes = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderPayload),
  });
  const order = await orderRes.json();
  if (!orderRes.ok) throw new Error(order.erro || "Não foi possível criar o pedido.");

  const payRes = await fetch(`/api/orders/${order.id}/pagamento`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method, ...extra }),
  });
  const payment = await payRes.json();
  if (!payRes.ok) throw new Error(payment.erro || "Não foi possível processar o pagamento.");

  return { order, payment };
}

function showSuccess(order, payment) {
  clearCart();
  contentEl.hidden = true;
  successEl.hidden = false;

  let msg = `Pedido #${order.id} confirmado`;
  if (payment.method === "cartao" && payment.installments > 1) {
    msg += ` — ${payment.installments}x, total de ${formatPrice(payment.amount)}`;
  } else {
    msg += ` — total de ${formatPrice(payment.amount)}`;
  }
  msg += ". Bom apetite!";
  document.getElementById("successMessage").textContent = msg;

  const codeEl = document.getElementById("successCode");
  if (payment.pix_copia_cola) {
    codeEl.hidden = false;
    codeEl.textContent = "Pix: " + payment.pix_copia_cola;
  } else if (payment.boleto_barcode) {
    codeEl.hidden = false;
    codeEl.textContent = `Boleto (vence em ${payment.boleto_due_date}): ${payment.boleto_barcode}`;
  } else {
    codeEl.hidden = true;
  }
}

/* Cartão novo */
cardForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("paymentError");
  const btn = document.getElementById("paySubmitBtn");
  errorEl.textContent = "";
  btn.disabled = true; btn.textContent = "Processando...";

  try {
    const { order, payment } = await createOrderAndPay("cartao", {
      card_name: document.getElementById("cardName").value,
      card_number: cardNumberInput.value,
      expiry: cardExpiryInput.value,
      cvv: document.getElementById("cardCvv").value,
      installments: parseInt(document.getElementById("installments").value, 10),
      save_card: document.getElementById("saveCard").checked,
    });
    showSuccess(order, payment);
  } catch (err) {
    errorEl.textContent = err.message;
    btn.disabled = false; btn.textContent = "Pagar agora";
  }
});

/* Cartão salvo */
savedCardForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("savedCardError");
  const btn = savedCardForm.querySelector(".payment-submit");
  errorEl.textContent = "";
  btn.disabled = true; btn.textContent = "Processando...";

  try {
    const { order, payment } = await createOrderAndPay("cartao", {
      card_id: selectedCardId,
      cvv: document.getElementById("savedCvv").value,
      installments: parseInt(document.getElementById("savedInstallments").value, 10),
    });
    showSuccess(order, payment);
  } catch (err) {
    errorEl.textContent = err.message;
    btn.disabled = false; btn.textContent = "Pagar agora";
  }
});

/* Pix */
document.getElementById("pixConfirmBtn").addEventListener("click", async () => {
  const errorEl = document.getElementById("pixError");
  const btn = document.getElementById("pixConfirmBtn");
  errorEl.textContent = "";
  btn.disabled = true; btn.textContent = "Processando...";

  try {
    const { order, payment } = await createOrderAndPay("pix", {});
    showSuccess(order, payment);
  } catch (err) {
    errorEl.textContent = err.message;
    btn.disabled = false; btn.textContent = "Gerar Pix e confirmar";
  }
});

/* Boleto */
document.getElementById("boletoConfirmBtn").addEventListener("click", async () => {
  const errorEl = document.getElementById("boletoError");
  const btn = document.getElementById("boletoConfirmBtn");
  errorEl.textContent = "";
  btn.disabled = true; btn.textContent = "Processando...";

  try {
    const { order, payment } = await createOrderAndPay("boleto", {});
    showSuccess(order, payment);
  } catch (err) {
    errorEl.textContent = err.message;
    btn.disabled = false; btn.textContent = "Gerar boleto e confirmar";
  }
});

init();
