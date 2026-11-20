
import hashlib
from io import BytesIO

import pandas as pd


def ler_arquivo(arquivo):
    nome = arquivo.name.lower()
    conteudo = arquivo.getvalue()

    if nome.endswith(".csv"):
        try:
            return pd.read_csv(
                BytesIO(conteudo),
                sep=None,
                engine="python",
                encoding="utf-8-sig",
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                BytesIO(conteudo),
                sep=None,
                engine="python",
                encoding="latin1",
            )

    if nome.endswith(".xlsx"):
        return pd.read_excel(
            BytesIO(conteudo),
            engine="openpyxl",
        )

    raise ValueError("Formato de arquivo não suportado.")


def calcular_hash_arquivo(arquivo, banco_origem):
    conteudo = arquivo.getvalue()

    return hashlib.sha256(
        banco_origem.encode("utf-8") + b":" + conteudo
    ).hexdigest()
