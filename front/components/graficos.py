
import pandas as pd
import streamlit as st

from services.movimentacoes import converter_valor_monetario


def render_grafico_evolucao(df, coluna_data, coluna_tipo):
    """Exibe a evolução mensal de entradas, saídas e saldo acumulado."""

    st.subheader("Evolução financeira mensal")

    if df.empty:
        st.info("Não existem movimentações para gerar o gráfico.")
        return

    if not coluna_data or coluna_data not in df.columns:
        st.warning("Não foi possível identificar a coluna de datas.")
        return

    if not coluna_tipo or coluna_tipo not in df.columns:
        st.warning("Não foi possível identificar a coluna de tipo de lançamento.")
        return

    if "Valor" not in df.columns:
        st.warning("A coluna 'Valor' não foi encontrada.")
        return

    # Prepara os dados
    dados = df.copy()

    dados["data"] = pd.to_datetime(
        dados[coluna_data],
        errors="coerce",
        dayfirst=True
    )

    dados["valor"] = dados["Valor"].apply(
        converter_valor_monetario
    )

    dados["tipo"] = (
        dados[coluna_tipo]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    # Identifica o mês e ano de cada movimentação
    dados["periodo"] = dados["data"].dt.to_period("M")

    dados = dados.dropna(subset=["periodo"])

    if dados.empty:
        st.info("Não existem datas válidas para gerar o gráfico.")
        return

    # Calcula entradas e saídas mensais
    dados["entradas"] = dados["valor"].where(
        dados["tipo"] == "entrada",
        0
    )

    dados["saidas"] = dados["valor"].abs().where(
        dados["tipo"] == "saída",
        0
    )

    # Agrupa os valores por mês
    grafico = (
        dados.groupby("periodo")[["entradas", "saidas"]]
        .sum()
        .sort_index()
    )

    # Preenche meses sem movimentações com zero
    todos_periodos = pd.period_range(
        start=grafico.index.min(),
        end=grafico.index.max(),
        freq="M"
    )

    grafico = grafico.reindex(
        todos_periodos,
        fill_value=0
    )

    # Calcula o saldo mensal
    saldo_mensal = grafico["entradas"] - grafico["saidas"]

    # Calcula o saldo acumulado
    grafico["saldo"] = saldo_mensal.cumsum()

    # Organiza os nomes das séries
    grafico = grafico.rename(
        columns={
            "entradas": "Entradas",
            "saidas": "Saídas",
            "saldo": "Saldo acumulado"
        }
    )

    # Transforma o período em data para o eixo horizontal
    grafico.index = grafico.index.to_timestamp()
    grafico.index.name = "Mês"

    # Exibe o gráfico
    st.line_chart(
        grafico,
        x_label="Mês",
        y_label="Valor (R$)",
        height=450
    )

    st.caption(
        "Entradas e saídas são exibidas mensalmente. "
        "O saldo considera o resultado acumulado dos meses anteriores."
    )
