"""
Camada Model — validação e regras de cartão de crédito.

Isto continua sendo uma simulação (não há gateway real por trás), mas
agora com validações de verdade:
- Algoritmo de Luhn, o mesmo usado por bandeiras reais para detectar
  números de cartão digitados errado.
- Identificação de bandeira pelo prefixo (BIN) do cartão.
- Cálculo de parcelas com juros simples para 4x ou mais, como a
  maioria dos e-commerces brasileiros faz.
"""
import re


def luhn_valido(numero):
    """Algoritmo de Luhn: soma dígitos alternadamente dobrados, válido
    se o total for múltiplo de 10."""
    digits = [int(d) for d in numero]
    checksum = 0
    should_double = False
    for d in reversed(digits):
        if should_double:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
        should_double = not should_double
    return checksum % 10 == 0


def identificar_bandeira(numero):
    """Identifica a bandeira pelos primeiros dígitos (BIN). Cobre as
    faixas mais comuns; fora delas, retorna 'desconhecida' (o
    pagamento simulado continua funcionando normalmente)."""
    if re.match(r"^4", numero):
        return "visa"
    if re.match(r"^5[1-5]", numero) or re.match(r"^2(2[2-9]|[3-6]\d|7[01]|720)", numero):
        return "mastercard"
    if re.match(r"^3[47]", numero):
        return "amex"
    if re.match(r"^(4011|4312|4389|4514|4573|6277|6362|6363|650|6516|6550)", numero):
        return "elo"
    return "desconhecida"


def calcular_parcelas(total, parcelas):
    """
    Até 3x: sem juros (valor dividido igualmente).
    De 4x a 12x: juros simples de 1,99% ao mês sobre o total.
    Retorna (valor_de_cada_parcela, total_com_juros).
    """
    parcelas = max(1, min(int(parcelas), 12))

    if parcelas <= 3:
        valor_parcela = round(total / parcelas, 2)
        return valor_parcela, total

    taxa_mensal = 0.0199
    total_com_juros = round(total * ((1 + taxa_mensal) ** parcelas), 2)
    valor_parcela = round(total_com_juros / parcelas, 2)
    return valor_parcela, total_com_juros
