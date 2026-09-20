/**
 * Toast simples e reutilizável — substitui mensagens de texto estático
 * por um feedback rápido, visual e que some sozinho. Chame
 * showToast("mensagem") de qualquer página que já tenha esse arquivo
 * incluído.
 */
function showToast(message, kind = "success") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast toast-" + kind;
  toast.textContent = message;
  container.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add("toast-in"));

  setTimeout(() => {
    toast.classList.remove("toast-in");
    toast.classList.add("toast-out");
    setTimeout(() => toast.remove(), 250);
  }, 2800);
}
