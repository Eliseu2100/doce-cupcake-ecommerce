# Hospedagem — repositório Git pronto para o Render

Este projeto já vem com um repositório Git inicializado (pasta `.git`)
e um `render.yaml` (Render Blueprint), então o caminho mais rápido é:

## Passo a passo

1. **Crie um repositório vazio no GitHub** (sem README, sem
   `.gitignore` — ele já vem daqui): [github.com/new](https://github.com/new)

2. **Aponte este repositório local para o GitHub e envie:**
   ```bash
   cd doce_cupcake_backend
   git remote add origin https://github.com/SEU-USUARIO/doce-cupcake.git
   git branch -M main
   git push -u origin main
   ```
   (o histórico de commits já está pronto, você só precisa do `push`)

3. **No Render:**
   - Acesse [render.com](https://render.com) e faça login com o GitHub
   - Clique em **New → Blueprint**
   - Selecione o repositório `doce-cupcake` que você acabou de subir
   - O Render lê o `render.yaml` automaticamente e já preenche:
     - Build command: `pip install -r requirements.txt`
     - Start command: `gunicorn app:app`
     - Variáveis `SECRET_KEY` e `APP_ENCRYPTION_KEY` geradas automaticamente
   - Clique em **Apply** / **Create**

4. Em poucos minutos você recebe uma URL pública, algo como
   `https://doce-cupcake.onrender.com`.

### Sobre o disco persistente (SQLite)

O `render.yaml` já inclui um disco persistente para o
`database/cupcake.db` não se perder a cada reinício — mas discos
persistentes só existem nos **planos pagos** do Render. Se você for
usar o plano gratuito:

- Abra o `render.yaml` e apague o bloco `disk:` no final do arquivo
  antes de subir (ou apenas ignore o aviso do Render sobre isso)
- A aplicação funciona normalmente; o único efeito é que o banco volta
  ao cardápio inicial de demonstração sempre que o serviço reinicia
  por inatividade (comportamento normal do plano free, não é um bug)

---

# Por que não Netlify?

## Por que o Netlify não serve para este projeto

O Netlify foi feito para **sites estáticos** (HTML/CSS/JS puro) e para
**funções serverless** de vida curta. Este projeto é diferente: é uma
aplicação **Flask** que roda continuamente, guarda estado (o carrinho
vira pedido, o pedido vira pagamento) e escreve num arquivo de banco
**SQLite** (`database/cupcake.db`).

Dois problemas tornam isso incompatível com o Netlify:

1. **Sistema de arquivos efêmero.** Cada função do Netlify roda num
   container que é descartado depois da execução. O arquivo
   `cupcake.db` seria recriado do zero (ou simplesmente perdido) a
   cada nova invocação — os cadastros, pedidos e pagamentos
   desapareceriam.
2. **Sem servidor persistente.** O Flask precisa ficar "no ar",
   escutando requisições e mantendo a sessão de login (cookie) entre
   uma chamada e outra. O modelo do Netlify não foi pensado para isso.

Ou seja: não é uma questão de configuração — é a arquitetura do
Netlify que não é a ferramenta certa para uma aplicação Flask +
SQLite com login e banco de dados real.

## O que usar em vez do Netlify

Qualquer serviço que rode um processo Python continuamente resolve. O
Render (seção acima) já é a opção recomendada e vem pronta neste
projeto. Alternativas equivalentes, caso prefira:

### PythonAnywhere

Pensado especificamente para hospedar Python, com sistema de arquivos
persistente de verdade no plano gratuito — bom para manter o SQLite
como está, sem precisar trocar de banco.

1. Crie conta em [pythonanywhere.com](https://www.pythonanywhere.com)
2. Suba os arquivos do projeto (upload manual ou `git clone` pelo
   console Bash deles)
3. Configure uma "Web App" apontando para `app.py` (WSGI via Flask)
4. `pip install -r requirements.txt` no console deles

### Railway.app

Parecido com o Render (build automático a partir do Git), com disco
persistente incluso no plano gratuito por um tempo — bom para manter
o SQLite sem migração.

## E o Netlify, fica sem função nenhuma?

Se o objetivo for só ter uma **página de divulgação estática** (sem
login, carrinho ou banco de dados reais) para compartilhar um link
rápido, aí sim o Netlify funciona bem — bastaria gerar uma versão
"demo" só de front-end, sem chamadas à API. Mas isso não seria o
projeto completo com back-end MVC que foi pedido; seria uma versão
reduzida, só para vitrine.
