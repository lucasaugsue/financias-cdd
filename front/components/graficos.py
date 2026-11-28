
import pandas as pd
import streamlit as st

from api.categorias import listar_categorias
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


def render_grafico_categorias(df):

    usuario_id = st.session_state["usuario"]["id"]

    st.subheader("Análise por categorias")

    if "categoria_id" not in df.columns:
        st.warning("Não foi possível identificar as categorias.")
        return

    # Busca somente as categorias do usuário autenticado
    categorias = listar_categorias(usuario_id)

    if not categorias:
        st.info("Nenhuma categoria cadastrada.")
        return

    df_categorias = pd.DataFrame(categorias)

    dados = df[
        df["categoria_id"].notna()
    ].copy()

    if dados.empty:
        st.info("Ainda não existem movimentações categorizadas.")
        return

    dados = dados.merge(
        df_categorias[["id", "categoria", "finalidade"]],
        left_on="categoria_id",
        right_on="id",
        how="inner"
    )

    # Divide o conteúdo em duas colunas
    coluna_grafico, coluna_detalhamento = st.columns(
        [2, 1],
        gap="large"
    )

    # Seletor fica somente na coluna de detalhamento
    with coluna_detalhamento:

        tipo_analise = st.selectbox(
            "Selecione o tipo",
            ["Despesas", "Receitas"],
            key=f"seletor_tipo_categorias_{usuario_id}"
        )

    # Filtra receitas ou despesas
    finalidade = (
        "Receita"
        if tipo_analise == "Receitas"
        else "Despesa"
    )

    dados = dados[
        dados["finalidade"].isin([finalidade, "Ambas"])
    ]

    # Identifica a coluna de fluxo financeiro.
    if "Fluxo" not in dados.columns:
        st.warning("Não foi possível identificar o fluxo financeiro.")
        return

    fluxo_lancamento = (
        "entrada"
        if tipo_analise == "Receitas"
        else "saída"
    )

    dados = dados[
        dados["Fluxo"].astype(str).str.strip().str.casefold()
        == fluxo_lancamento
    ]


    if dados.empty:
        with coluna_grafico:
            st.info(f"Não existem {tipo_analise.lower()} categorizadas.")
        return

    # Converte os valores monetários
    dados["valor"] = dados["Valor"].apply(
        converter_valor_monetario
    ).abs()

    # Agrupa valores por categoria
    grafico = (
        dados.groupby("categoria")["valor"]
        .sum()
        .sort_values(ascending=False)
    )

    # Gráfico de pizza
    with coluna_grafico:

        st.write("**Distribuição por categoria**")

        st.plotly_chart(
            {
                "data": [
                    {
                        "type": "pie",
                        "labels": grafico.index.tolist(),
                        "values": grafico.values.tolist(),
                        "hole": 0.35,
                    }
                ],
                "layout": {
                    "showlegend": True,
                    "margin": {
                        "t": 10,
                        "b": 10,
                        "l": 10,
                        "r": 10
                    },
                },
            },
            width='stretch'
        )

    # Detalhamento abaixo do seletor
    with coluna_detalhamento:

        st.write("**Detalhamento**")

        df_detalhamento = pd.DataFrame({
            "Categoria": grafico.index,
            "Valor": grafico.values,
        })

        df_detalhamento["Valor"] = df_detalhamento["Valor"].apply(
            lambda valor: (
                "R$ "
                + f"{valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        )

        st.dataframe(
            df_detalhamento,
            width="stretch",
            hide_index=True,
            height=450
        )
