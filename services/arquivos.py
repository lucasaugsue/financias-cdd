
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
    

def limpar_extrato_banco_brasil(df):
    """
    Aplica regras específicas aos extratos CSV do Banco do Brasil:
    - Remove movimentações com valor igual a zero.
    - Remove lançamentos BB Rende Fácil.
    """
    df = df.copy()

    # Regra 1: remover BB Rende Fácil
    if "Lançamento" in df.columns:
        lancamentos = (
            df["Lançamento"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        df = df[lancamentos != "bb rende fácil"]

    # Regra 2: remover valores iguais a zero
    if "Valor" in df.columns:

        def converter_valor(valor):
            if pd.isna(valor):
                return float("nan")

            if isinstance(valor, (int, float)):
                return float(valor)

            valor = str(valor).strip()
            valor = valor.replace("R$", "").replace(" ", "")

            if "," in valor and "." in valor:
                if valor.rfind(",") > valor.rfind("."):
                    valor = valor.replace(".", "").replace(",", ".")
                else:
                    valor = valor.replace(",", "")
            elif "," in valor:
                valor = valor.replace(",", ".")

            return pd.to_numeric(valor, errors="coerce")

        valores = df["Valor"].apply(converter_valor)

        # Mantém valores não identificados e remove somente os zeros.
        df = df[valores.isna() | valores.ne(0)]

    return df.reset_index(drop=True)

