"""
Camada Model — processamento de pagamento.

Importante: isto continua sendo um pagamento SIMULADO, para fins
acadêmicos — não há integração com nenhuma operadora, banco ou Pix
real por trás. O que melhora aqui é a qualidade da simulação:

- Cartão: valida o número com o algoritmo de Luhn (o mesmo que
  bandeiras reais usam para pegar erro de digitação), identifica a
  bandeira pelo prefixo, e calcula parcelamento com juros simples a
  partir de 4x — como a maioria dos e-commerces brasileiros.
- Pix: gera um código "Copia e Cola" no formato EMV oficial do Banco
  Central (com CRC16 válido), só que com uma chave Pix fictícia.
- Boleto: gera uma linha digitável de 47 dígitos com os mesmos
  dígitos verificadores (módulo 10 e módulo 11) de um boleto real,
  sem registro em banco nenhum por trás.

Em nenhum caso o número completo do cartão ou o CVV são gravados no
banco — só os 4 últimos dígitos e a bandeira.
"""
import re
from datetime import datetime, timedelta
from models.database import get_db
from models.order_model import OrderModel
from models.card_model import CardModel
from models.card_service import luhn_valido, identificar_bandeira, calcular_parcelas
from models.pix_service import PixService
from models.boleto_service import BoletoService
from models.coupon_model import CouponModel

CVV_REGEX = re.compile(r"^\d{3,4}$")
EXPIRY_REGEX = re.compile(r"^(0[1-9]|1[0-2])\/(\d{2})$")


def _cvv_len_esperado(bandeira):
    return 4 if bandeira == "amex" else 3


class PaymentModel:

    @staticmethod
    def process(order_id, user_id, method, card_id=None, card_number=None, card_name=None,
                expiry=None, cvv=None, save_card=False, installments=1):
        """
        Processa (de forma simulada) o pagamento de um pedido já existente.
        Lança ValueError se os dados forem inválidos ou o pedido não existir.
        Retorna um dicionário com o resultado do pagamento.
        """
        order = OrderModel.get_by_id(order_id)
        if order is None:
            raise ValueError("Pedido não encontrado.")
        if order["status"] == "pago":
            raise ValueError("Este pedido já foi pago.")

        if method not in ("cartao", "pix", "boleto"):
            raise ValueError("Forma de pagamento inválida.")

        db = get_db()
        created_at = datetime.now().isoformat(timespec="seconds")

        card_last4 = None
        card_brand = None
        parcelas_qtd = 1
        valor_cobrado = order["total"]
        pix_copia_cola = None
        boleto_barcode = None
        boleto_due_date = None

        if method == "cartao":
            if not cvv or not CVV_REGEX.match(cvv):
                raise ValueError("CVV inválido.")

            if card_id:
                # Cartão já salvo: só confirmamos com o CVV (o número
                # completo nunca fica guardado, então não há como
                # "recarregá-lo" — é assim que funciona até em cartão
                # salvo de sistemas reais).
                saved = CardModel.get_by_id_for_user(card_id, user_id)
                if saved is None:
                    raise ValueError("Cartão salvo não encontrado.")
                card_last4 = saved["last4"]
                card_brand = saved["brand"]
            else:
                digits = re.sub(r"\D", "", card_number or "")
                if len(digits) < 13 or len(digits) > 19:
                    raise ValueError("Número de cartão inválido.")
                if not luhn_valido(digits):
                    raise ValueError("Número de cartão inválido (não passou na validação).")
                if not card_name or len(card_name.strip()) < 3:
                    raise ValueError("Informe o nome impresso no cartão.")
                if not expiry or not EXPIRY_REGEX.match(expiry):
                    raise ValueError("Validade inválida. Use o formato MM/AA.")

                card_brand = identificar_bandeira(digits)
                card_last4 = digits[-4:]

                if save_card:
                    CardModel.create(user_id, digits, card_name, expiry)

            if _cvv_len_esperado(card_brand) != len(cvv):
                raise ValueError(f"CVV inválido para cartão {card_brand} (esperado {_cvv_len_esperado(card_brand)} dígitos).")

            parcelas_qtd = max(1, min(int(installments or 1), 12))
            _, valor_cobrado = calcular_parcelas(order["total"], parcelas_qtd)

        elif method == "pix":
            pix_copia_cola = PixService.gerar_copia_e_cola(order_id, order["total"])

        elif method == "boleto":
            vencimento = (datetime.now() + timedelta(days=3)).date()
            boleto_barcode = BoletoService.gerar(order_id, order["total"], vencimento)
            boleto_due_date = vencimento.isoformat()

        status = "aprovado"

        db.execute(
            """INSERT INTO payments
               (order_id, method, card_last4, card_brand, installments,
                pix_copia_cola, boleto_barcode, boleto_due_date, amount, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, method, card_last4, card_brand, parcelas_qtd,
             pix_copia_cola, boleto_barcode, boleto_due_date, valor_cobrado, status, created_at),
        )
        db.execute("UPDATE orders SET status = 'pago' WHERE id = ?", (order_id,))
        if order.get("coupon_code"):
            CouponModel.mark_used(order["coupon_code"], order_id)
        db.commit()

        return {
            "order_id": order_id,
            "method": method,
            "card_last4": card_last4,
            "card_brand": card_brand,
            "installments": parcelas_qtd,
            "pix_copia_cola": pix_copia_cola,
            "boleto_barcode": boleto_barcode,
            "boleto_due_date": boleto_due_date,
            "amount": valor_cobrado,
            "status": status,
            "created_at": created_at,
        }
