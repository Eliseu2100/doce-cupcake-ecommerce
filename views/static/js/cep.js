/**
 * Busca de endereço a partir do CEP (ViaCEP / Correios), via o nosso
 * back-end (GET /api/cep/<cep>). Reutilizado no cadastro e na etapa
 * de entrega — quem chama só passa os ids dos campos do formulário.
 */
function setupCepAutocomplete({ zipId, streetId, neighborhoodId, cityId, stateId, feedbackId }) {
  const zipInput = document.getElementById(zipId);
  if (!zipInput) return;
  const feedbackEl = feedbackId ? document.getElementById(feedbackId) : null;

  function setFeedback(text, kind) {
    if (!feedbackEl) return;
    feedbackEl.textContent = text;
    feedbackEl.className = "cep-feedback" + (kind ? " cep-feedback-" + kind : "");
  }

  async function fetchAndFill() {
    const digits = zipInput.value.replace(/\D/g, "");
    if (digits.length !== 8) return;

    setFeedback("Buscando endereço...", "loading");

    try {
      const res = await fetch(`/api/cep/${digits}`);
      const data = await res.json();

      if (!res.ok) {
        setFeedback(data.erro || "CEP não encontrado. Preencha manualmente.", "error");
        return;
      }

      const map = { [streetId]: data.street, [neighborhoodId]: data.neighborhood, [cityId]: data.city, [stateId]: data.state };
      Object.entries(map).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.value = value;
      });

      setFeedback("Endereço encontrado ✓", "ok");
    } catch (err) {
      setFeedback("Erro ao consultar o CEP. Preencha manualmente.", "error");
    }
  }

  zipInput.addEventListener("input", () => {
    zipInput.value = zipInput.value.replace(/\D/g, "").slice(0, 8);
  });
  zipInput.addEventListener("blur", fetchAndFill);
}
