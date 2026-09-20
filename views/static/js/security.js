/**
 * Escapa texto antes de inserir via innerHTML. Usado sempre que o
 * conteúdo vem de algo que o próprio usuário digitou (nome do
 * endereço, nome impresso no cartão etc.) — sem isso, alguém poderia
 * salvar um endereço com um "nome" tipo <script>...</script> e esse
 * código rodaria quando a página fosse renderizada de novo.
 */
function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}
