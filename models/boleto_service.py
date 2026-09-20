"""
Camada Model — geração de um boleto bancário SIMULADO.

Não existe integração com nenhum banco real. Geramos uma linha
digitável no MESMO FORMATO numérico de um boleto de verdade (47
dígitos, com dígitos verificadores por módulo 10 e módulo 11), só
para fins de demonstração do fluxo de pagamento por boleto — não é
registrável em banco nenhum.
"""
from datetime import date

BANCO_FICTICIO = "001"


def _modulo10(bloco):
    soma = 0
    peso = 2
    for digito in reversed(bloco):
        valor = int(digito) * peso
        if valor > 9:
            valor -= 9
        soma += valor
        peso = 1 if peso == 2 else 2
    resto = soma % 10
    return 0 if resto == 0 else 10 - resto


def _modulo11(sequencia):
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    for i, digito in enumerate(reversed(sequencia)):
        soma += int(digito) * pesos[i % len(pesos)]
    resto = soma % 11
    dv = 11 - resto
    return 1 if dv in (0, 10, 11) else dv


class BoletoService:

    @staticmethod
    def gerar(order_id, amount, due_date):
        # O "fator de vencimento" do padrão Febraban tem só 4 dígitos
        # (0 a 9999), contados a partir de 07/10/1997. Esse contador
        # passou de 9999 na vida real em fevereiro/2025 — o mesmo
        # estouro aconteceria aqui a partir dessa data. Aplicamos
        # módulo 10000 para o campo continuar com 4 dígitos (é uma
        # simplificação da correção que os bancos brasileiros adotaram).
        fator_vencimento = (due_date - date(1997, 10, 7)).days % 10000
        valor_str = f"{int(round(amount * 100)):010d}"
        campo_livre = (f"{order_id:010d}" + "0" * 15)[:25]

        bloco1_base = BANCO_FICTICIO + "9" + campo_livre[0:5]
        bloco2_base = campo_livre[5:15]
        bloco3_base = campo_livre[15:25]

        bloco1 = bloco1_base + str(_modulo10(bloco1_base))
        bloco2 = bloco2_base + str(_modulo10(bloco2_base))
        bloco3 = bloco3_base + str(_modulo10(bloco3_base))

        corpo_sem_dv = BANCO_FICTICIO + "9" + f"{fator_vencimento:04d}" + valor_str + campo_livre
        dv_geral = _modulo11(corpo_sem_dv)

        return (
            f"{bloco1[:5]}.{bloco1[5:]} "
            f"{bloco2[:5]}.{bloco2[5:]} "
            f"{bloco3[:5]}.{bloco3[5:]} "
            f"{dv_geral} {fator_vencimento:04d}{valor_str}"
        )
