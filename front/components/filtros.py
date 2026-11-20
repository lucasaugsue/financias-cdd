
import streamlit as st

from services.movimentacoes import aplicar_filtros


def limpar_filtros():

    st.session_state["filtro_banco"] = "Todos"
    st.session_state["filtro_tipo"] = "Todos"
    st.session_state["filtro_arquivo"] = "Todos"

    if "filtro_periodo_padrao" in st.session_state:
        st.session_state["filtro_periodo"] = (
            st.session_state["filtro_periodo_padrao"]
        )


def render_filtros(df, coluna_data, coluna_tipo):

    st.markdown("### Filtros")

    bancos = ["Todos"] + sorted(
        df["banco_origem"]
        .dropna()
        .unique()
        .tolist()
    )

    arquivos = ["Todos"] + sorted(
        df["arquivo_origem"]
        .dropna()
        .unique()
        .tolist()
    )

    periodo_disponivel = (
        coluna_data is not None
        and df[coluna_data].notna().any()
    )

    if periodo_disponivel:

        data_minima = df[coluna_data].min()
        data_maxima = df[coluna_data].max()

        periodo_padrao = (
            data_minima,
            data_maxima,
        )

        st.session_state["filtro_periodo_padrao"] = (
            periodo_padrao
        )

        if "filtro_periodo" not in st.session_state:
            st.session_state["filtro_periodo"] = (
                periodo_padrao
            )

        periodo_atual = st.session_state["filtro_periodo"]

        if (
            len(periodo_atual) != 2
            or periodo_atual[0] < data_minima
            or periodo_atual[1] > data_maxima
        ):
            st.session_state["filtro_periodo"] = (
                periodo_padrao
            )

    if "filtro_banco" not in st.session_state:
        st.session_state["filtro_banco"] = "Todos"

    if "filtro_tipo" not in st.session_state:
        st.session_state["filtro_tipo"] = "Todos"

    if "filtro_arquivo" not in st.session_state:
        st.session_state["filtro_arquivo"] = "Todos"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        banco = st.selectbox(
            "Banco",
            bancos,
            key="filtro_banco",
        )

    with col2:
        if periodo_disponivel:

            periodo = st.date_input(
                "Período",
                min_value=data_minima,
                max_value=data_maxima,
                format="DD/MM/YYYY",
                key="filtro_periodo",
            )

        else:
            periodo = None

            st.caption(
                "Coluna de data não encontrada."
            )

    with col3:
        if coluna_tipo:

            tipo = st.selectbox(
                "Tipo de lançamento",
                ["Todos", "Entrada", "Saída"],
                key="filtro_tipo",
            )

        else:
            tipo = "Todos"

            st.caption(
                "Campo Tipo Lançamento não encontrado."
            )

    with col4:
        arquivo = st.selectbox(
            "Arquivo de origem",
            arquivos,
            key="filtro_arquivo",
        )

    st.button(
        "🧹 Limpar filtros",
        on_click=limpar_filtros,
    )

    return aplicar_filtros(
        df=df,
        banco=banco,
        periodo=periodo,
        tipo=tipo,
        arquivo=arquivo,
        coluna_data=coluna_data,
        coluna_tipo=coluna_tipo,
    )
