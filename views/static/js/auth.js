/**
 * View das páginas de autenticação. Não guarda regra de negócio —
 * só envia os dados para o Controller (/api/auth/...) e trata a resposta.
 */
function getNextUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("next") || "/";
}

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const errorEl = document.getElementById("authError");

const addAddressNow = document.getElementById("addAddressNow");
const addressFields = document.getElementById("addressFields");
if (addAddressNow) {
  addAddressNow.addEventListener("change", () => {
    addressFields.hidden = !addAddressNow.checked;
  });
}

if (document.getElementById("zipCode")) {
  setupCepAutocomplete({
    zipId: "zipCode",
    streetId: "street",
    neighborhoodId: "neighborhood",
    cityId: "city",
    stateId: "state",
    feedbackId: "cepFeedback",
  });
}

async function submitAuth(url, payload, submitBtn) {
  errorEl.textContent = "";
  submitBtn.disabled = true;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.erro || "Não foi possível concluir. Tente novamente.";
      submitBtn.disabled = false;
      return;
    }

    window.location.href = getNextUrl();
  } catch (err) {
    errorEl.textContent = "Erro de conexão com o servidor.";
    submitBtn.disabled = false;
  }
}

if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitAuth(
      "/api/auth/login",
      {
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
      },
      loginForm.querySelector(".auth-submit")
    );
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const payload = {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      password: document.getElementById("password").value,
      phone: document.getElementById("phone").value,
      accepted_privacy: document.getElementById("acceptPrivacy").checked,
    };

    if (addAddressNow && addAddressNow.checked) {
      payload.address = {
        zip_code: document.getElementById("zipCode").value,
        street: document.getElementById("street").value,
        number: document.getElementById("number").value,
        complement: document.getElementById("complement").value,
        neighborhood: document.getElementById("neighborhood").value,
        city: document.getElementById("city").value,
        state: document.getElementById("state").value,
      };
    }

    submitAuth("/api/auth/register", payload, registerForm.querySelector(".auth-submit"));
  });
}

/* ---------------- Esqueci minha senha ---------------- */
const forgotForm = document.getElementById("forgotForm");
if (forgotForm) {
  forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = forgotForm.querySelector(".auth-submit");
    errorEl.textContent = "";
    btn.disabled = true;

    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: document.getElementById("email").value }),
      });
      const data = await res.json();

      if (!res.ok) {
        errorEl.textContent = data.erro || "Não foi possível gerar o link.";
        btn.disabled = false;
        return;
      }

      forgotForm.hidden = true;
      const box = document.getElementById("resetLinkBox");
      box.hidden = false;
      const link = `${window.location.origin}/redefinir-senha?token=${encodeURIComponent(data.reset_token)}`;
      const anchor = document.getElementById("resetLinkAnchor");
      anchor.href = link;
      anchor.textContent = link;
    } catch (err) {
      errorEl.textContent = "Erro de conexão com o servidor.";
      btn.disabled = false;
    }
  });
}

/* ---------------- Redefinir senha ---------------- */
const resetForm = document.getElementById("resetForm");
if (resetForm) {
  const token = new URLSearchParams(window.location.search).get("token");

  resetForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = resetForm.querySelector(".auth-submit");
    errorEl.textContent = "";

    if (!token) {
      errorEl.textContent = "Link inválido — peça uma nova recuperação de senha.";
      return;
    }

    btn.disabled = true;
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: document.getElementById("newPassword").value }),
      });
      const data = await res.json();

      if (!res.ok) {
        errorEl.textContent = data.erro || "Não foi possível redefinir a senha.";
        btn.disabled = false;
        return;
      }

      showToast("Senha redefinida! Faça login com a nova senha.");
      setTimeout(() => { window.location.href = "/login"; }, 1200);
    } catch (err) {
      errorEl.textContent = "Erro de conexão com o servidor.";
      btn.disabled = false;
    }
  });
}
