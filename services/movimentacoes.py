import pandas as pd

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

    # Filtro de mês/ano
    if periodos and coluna_data and coluna_data in df_filtrado.columns:
        datas = pd.to_datetime(
            df_filtrado[coluna_data],
            errors="coerce"
        )

        df_filtrado = df_filtrado[
            datas.dt.strftime("%Y-%m").isin(periodos)
        ]

    # Filtro de banco de origem
    if banco != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["banco_origem"] == banco
        ]

    # Filtro de tipo de lançamento
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