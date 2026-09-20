"""
Camada Model — geração do código Pix "Copia e Cola".

Segue o formato EMV QR Code definido pelo Banco Central para o Pix
(campos ID + tamanho + valor, terminando em CRC16). O código gerado é
estruturalmente válido, mas continua sendo uma SIMULAÇÃO: a chave Pix
usada é fictícia, não existe uma conta real recebendo por trás dela.
"""


def _campo(campo_id, valor):
    tamanho = f"{len(valor):02d}"
    return f"{campo_id}{tamanho}{valor}"


def _crc16_ccitt(payload):
    """CRC16-CCITT (polinômio 0x1021, valor inicial 0xFFFF) — o
    checksum exigido pelo padrão EMV QR Code usado pelo Pix."""
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


class PixService:
    MERCHANT_NAME = "DOCE CUPCAKE"
    MERCHANT_CITY = "SAO PAULO"
    PIX_KEY = "doce.cupcake@pagamento.com"

    @staticmethod
    def gerar_copia_e_cola(order_id, amount):
        txid = f"DOCECK{order_id}"[:25]
        amount_str = f"{amount:.2f}"

        conta_pix = _campo("00", "br.gov.bcb.pix") + _campo("01", PixService.PIX_KEY)
        dados_adicionais = _campo("05", txid)

        payload = (
            _campo("00", "01")
            + _campo("26", conta_pix)
            + _campo("52", "0000")
            + _campo("53", "986")
            + _campo("54", amount_str)
            + _campo("58", "BR")
            + _campo("59", PixService.MERCHANT_NAME[:25])
            + _campo("60", PixService.MERCHANT_CITY[:15])
            + _campo("62", dados_adicionais)
            + "6304"
        )

        return payload + _crc16_ccitt(payload)
