
import pandas as pd


def identificar_coluna_data(df):
    return next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().lower() in ["data", "date"]
        ),
        None,
    )


def identificar_coluna_tipo(df):
    return next(
        (
            coluna for coluna in df.columns
            if str(coluna).strip().casefold() == "tipo lançamento".casefold()
        ),
        None,
    )


def preparar_movimentacoes(df):
    df = df.copy()

    coluna_data = identificar_coluna_data(df)
    coluna_tipo = identificar_coluna_tipo(df)

    if coluna_data:
        df[coluna_data] = pd.to_datetime(
            df[coluna_data], errors="coerce"
        ).dt.date

    return df, coluna_data, coluna_tipo


def aplicar_filtros(
    df,
    banco="Todos",
    periodo=None,
    tipo="Todos",
    arquivo="Todos",
    coluna_data=None,
    coluna_tipo=None,
):
    df_filtrado = df.copy()

    if banco != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["banco_origem"] == banco
        ]

    if coluna_data and periodo and len(periodo) == 2:
        data_inicio, data_final = periodo

        df_filtrado = df_filtrado[
            df_filtrado[coluna_data].between(data_inicio, data_final)
        ]

    if coluna_tipo and tipo != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado[coluna_tipo]
            .astype(str)
            .str.strip()
            .str.casefold() == tipo.casefold()
        ]

    if arquivo != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["arquivo_origem"] == arquivo
        ]

    return df_filtrado


def converter_valor_monetario(valor):
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


def calcular_indicadores(df, coluna_tipo, coluna_valor="Valor"):
    if coluna_valor not in df.columns:
        raise ValueError(
            f"A coluna '{coluna_valor}' não foi encontrada."
        )

    valores = df[coluna_valor].apply(converter_valor_monetario)

    tipos = (
        df[coluna_tipo]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    entradas = valores[tipos == "entrada"].sum()
    saidas = valores[tipos == "saída"].abs().sum()

    return {
        "total_movimentacoes": len(df),
        "total_entradas": entradas,
        "total_saidas": saidas,
    }
