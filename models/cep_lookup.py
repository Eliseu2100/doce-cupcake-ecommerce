"""
Camada Model — consulta de CEP via ViaCEP (serviço público que usa a
base de dados dos Correios).

Não persiste nada no banco: só busca o endereço a partir do CEP para
preencher o formulário automaticamente. Erros de rede ou CEP inválido
viram ValueError, para o Controller devolver uma mensagem amigável em
vez de quebrar a aplicação.
"""
import json
import re
import urllib.request
import urllib.error

CEP_REGEX = re.compile(r"^\d{8}$")
VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT_SECONDS = 5


class CepLookup:

    @staticmethod
    def buscar(cep):
        cep_digits = re.sub(r"\D", "", cep or "")
        if not CEP_REGEX.match(cep_digits):
            raise ValueError("CEP inválido. Informe os 8 dígitos.")

        url = VIACEP_URL.format(cep=cep_digits)
        request = urllib.request.Request(url, headers={"User-Agent": "doce-cupcake-app"})

        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError):
            raise ValueError("Não foi possível consultar o CEP agora. Tente novamente ou preencha manualmente.")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Resposta inválida do serviço de CEP.")

        if data.get("erro"):
            raise ValueError("CEP não encontrado.")

        return {
            "zip_code": cep_digits,
            "street": data.get("logradouro", ""),
            "neighborhood": data.get("bairro", ""),
            "city": data.get("localidade", ""),
            "state": data.get("uf", ""),
        }
