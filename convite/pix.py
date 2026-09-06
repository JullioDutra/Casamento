"""
Geração do payload PIX no padrão "Copia e Cola" (BR Code / EMV) e do
QR Code correspondente, para que cada presente da lista gere um QR Code
PIX real e escaneável — em vez do desenho estático de exemplo.
"""
import base64
import io

import qrcode


def _crc16_ccitt(payload: str) -> str:
    """Calcula o CRC16-CCITT (polinômio 0x1021) exigido no final do payload PIX."""
    polinomio = 0x1021
    resultado = 0xFFFF
    for byte in payload.encode("utf-8"):
        resultado ^= byte << 8
        for _ in range(8):
            if resultado & 0x8000:
                resultado = ((resultado << 1) ^ polinomio) & 0xFFFF
            else:
                resultado = (resultado << 1) & 0xFFFF
    return format(resultado, "04X")


def _campo(id_: str, valor: str) -> str:
    """Formata um campo no padrão TLV (ID + tamanho com 2 dígitos + valor) do EMV."""
    tamanho = str(len(valor)).zfill(2)
    return f"{id_}{tamanho}{valor}"


def gerar_payload_pix(chave: str, nome_recebedor: str, cidade: str, valor=None,
                       descricao: str = "", txid: str = "***") -> str:
    """
    Monta a string "Copia e Cola" do PIX (BR Code) seguindo o padrão do Banco
    Central. Se `valor` for None, o QR Code fica sem valor fixo (o pagador
    digita o valor no app do banco) — útil para presentes de "Valor Livre".
    """
    nome_recebedor = (nome_recebedor or "NOIVOS")[:25]
    cidade = (cidade or "BRASIL")[:15]
    txid = (txid or "***")[:25]

    gui = _campo("00", "BR.GOV.BCB.PIX")
    chave_campo = _campo("01", chave)
    info_adicional = _campo("02", descricao[:40]) if descricao else ""
    merchant_account_info = _campo("26", gui + chave_campo + info_adicional)

    payload = (
        _campo("00", "01")           # Payload Format Indicator
        + _campo("01", "11")          # Point of Initiation Method (11 = estático/reutilizável)
        + merchant_account_info       # Dados da chave PIX
        + _campo("52", "0000")        # Merchant Category Code
        + _campo("53", "986")         # Moeda: Real (BRL)
    )
    if valor is not None:
        payload += _campo("54", f"{float(valor):.2f}")
    payload += (
        _campo("58", "BR")
        + _campo("59", nome_recebedor)
        + _campo("60", cidade)
        + _campo("62", _campo("05", txid))
    )
    payload += "6304"  # ID + tamanho do CRC (o valor do CRC é calculado abaixo)
    return payload + _crc16_ccitt(payload)


def gerar_qrcode_base64(payload: str) -> str:
    """Gera a imagem do QR Code a partir do payload e retorna como PNG em base64."""
    img = qrcode.make(payload, box_size=8, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
