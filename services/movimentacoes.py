
import pandas as pd

from api.categorias import (
    listar_regras_categorizacao,
    listar_categorias,
)


def identificar_coluna_data(df):
    """Identifica a coluna que contém as datas das movimentações."""
    return next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().lower() in ["data", "date"]
        ),
        None,
    )


def identificar_coluna_tipo(df):
    """Identifica a coluna de tipo de lançamento."""
    return next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().casefold()
            == "tipo lançamento".casefold()
        ),
        None,
    )


def categorizar_movimentacoes(df, usuario_id):
    """Categoriza movimentações usando as regras do usuário."""

    df = df.copy()

    coluna_detalhes = next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().casefold() == "detalhes"
        ),
        None,
    )

    coluna_lancamento = next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().casefold() == "lançamento"
        ),
        None,
    )

    # Consultar somente categorias e regras do usuário
    categorias = listar_categorias(usuario_id)
    regras = listar_regras_categorizacao(usuario_id)

    # Relacionar ID com nome da categoria
    nomes_categorias = {
        categoria["id"]: categoria["categoria"]
        for categoria in categorias
    }

    # Priorizar palavras-chave mais específicas
    regras = sorted(
        regras,
        key=lambda regra: len(regra["palavra_chave"].strip()),
        reverse=True,
    )

    # Preservar categorias já existentes
    if "categoria_id" not in df.columns:
        df["categoria_id"] = None

    if "categoria" not in df.columns:
        df["categoria"] = None

    if "palavra_chave_identificada" not in df.columns:
        df["palavra_chave_identificada"] = None

    # Recuperar o nome das categorias já salvas
    for indice, movimentacao in df.iterrows():
        categoria_id = movimentacao["categoria_id"]

        if pd.notna(categoria_id):
            categoria_id = int(categoria_id)

            df.at[indice, "categoria_id"] = categoria_id
            df.at[indice, "categoria"] = nomes_categorias.get(
                categoria_id,
                movimentacao["categoria"]
            )

    # Categorizar somente movimentações pendentes
    for indice, movimentacao in df.iterrows():

        if pd.notna(movimentacao["categoria_id"]):
            continue

        textos = []

        for coluna in [coluna_detalhes, coluna_lancamento]:
            if coluna:
                valor = movimentacao[coluna]

                if pd.notna(valor):
                    textos.append(str(valor).casefold())

        texto_busca = " ".join(textos)

        for regra in regras:

            palavra = regra["palavra_chave"].strip().casefold()

            if palavra and palavra in texto_busca:
                df.at[indice, "categoria_id"] = regra["categoria_id"]
                df.at[indice, "categoria"] = regra["categoria"]
                df.at[indice, "palavra_chave_identificada"] = (
                    regra["palavra_chave"]
                )

                break

    return df


def preparar_movimentacoes(df):
    df = df.copy()

    coluna_data = identificar_coluna_data(df)
    coluna_tipo = identificar_coluna_tipo(df)

    if coluna_data:
        df[coluna_data] = pd.to_datetime(
            df[coluna_data],
            errors="coerce",
            dayfirst=True
        ).dt.date

    return df, coluna_data, coluna_tipo


def listar_periodos_disponiveis(df, coluna_data):
    """Retorna os meses/anos que possuem movimentações cadastradas."""

    if not coluna_data or coluna_data not in df.columns:
        return []

    datas = pd.to_datetime(
        df[coluna_data],
        errors="coerce"
    )

    periodos = (
        datas.dt.to_period("M")
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    return sorted(periodos, reverse=True)


def aplicar_filtros(
    df,
    banco="Todos",
    periodos=None,
    tipo="Todos",
    coluna_data=None,
    coluna_tipo=None,
):
    """Aplica os filtros selecionados nas movimentações."""

    df_filtrado = df.copy()

    if periodos and coluna_data and coluna_data in df_filtrado.columns:
        datas = pd.to_datetime(
            df_filtrado[coluna_data],
            errors="coerce"
        )

        df_filtrado = df_filtrado[
            datas.dt.strftime("%Y-%m").isin(periodos)
        ]

    if banco != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["banco_origem"] == banco
        ]

    if coluna_tipo and tipo != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado[coluna_tipo]
            .astype(str)
            .str.strip()
            .str.casefold()
            == tipo.casefold()
        ]

    return df_filtrado


def converter_valor_monetario(valor):
    """Converte valores monetários brasileiros para números."""

    if pd.isna(valor):
        return 0.0

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

    return float(valor)


def calcular_indicadores(
    df,
    coluna_tipo,
    coluna_valor="Valor"
):
    """Calcula os indicadores financeiros das movimentações."""

    if df.empty:
        return {
            "total_movimentacoes": 0,
            "total_entradas": 0.0,
            "total_saidas": 0.0,
            "saldo": 0.0,
        }

    if coluna_valor not in df.columns:
        raise ValueError(
            f"A coluna '{coluna_valor}' não foi encontrada."
        )

    if not coluna_tipo or coluna_tipo not in df.columns:
        raise ValueError(
            "A coluna de tipo de lançamento não foi encontrada."
        )

    valores = df[coluna_valor].apply(
        converter_valor_monetario
    )

    tipos = (
        df[coluna_tipo]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    entradas = valores[tipos == "entrada"].sum()
    saidas = valores[tipos == "saída"].abs().sum()
    saldo = entradas - saidas

    return {
        "total_movimentacoes": len(df),
        "total_entradas": entradas,
        "total_saidas": saidas,
        "saldo": saldo,
    }
