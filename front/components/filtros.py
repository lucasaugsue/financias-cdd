
import streamlit as st

from services.movimentacoes import aplicar_filtros


def limpar_filtros(periodo_padrao):
    """Restaura os filtros para os valores iniciais."""
    st.session_state["filtro_banco"] = "Todos"
    st.session_state["filtro_tipo"] = "Todos"
    st.session_state["filtro_arquivo_unico"] = "Todos"
    st.session_state["filtro_periodo"] = periodo_padrao


def render_filtros(df, coluna_data, coluna_tipo):

    # Identifica as opções disponíveis
    bancos = sorted(
        df["banco_origem"].dropna().unique().tolist()
    )

    arquivos = sorted(
        df["arquivo_origem"].dropna().unique().tolist()
    )

    tipos = []

    if coluna_tipo:
        tipos = sorted(
            df[coluna_tipo].dropna().astype(str).unique().tolist()
        )

    # Opções dos filtros
    opcoes_bancos = ["Todos"] + bancos
    opcoes_arquivos = ["Todos"] + arquivos
    opcoes_tipos = ["Todos"] + tipos

    # Define o período padrão
    if coluna_data and not df[coluna_data].dropna().empty:
        data_minima = df[coluna_data].min()
        data_maxima = df[coluna_data].max()

        periodo_padrao = (data_minima, data_maxima)
    else:
        periodo_padrao = None

    # Inicializa os estados
    if "filtro_banco" not in st.session_state:
        st.session_state["filtro_banco"] = "Todos"

    if "filtro_tipo" not in st.session_state:
        st.session_state["filtro_tipo"] = "Todos"

    if "filtro_arquivo_unico" not in st.session_state:
        st.session_state["filtro_arquivo_unico"] = "Todos"

    if "filtro_periodo" not in st.session_state:
        st.session_state["filtro_periodo"] = periodo_padrao

    # Corrige seleções que não existem mais nas opções
    if st.session_state["filtro_banco"] not in opcoes_bancos:
        st.session_state["filtro_banco"] = "Todos"

    if st.session_state["filtro_tipo"] not in opcoes_tipos:
        st.session_state["filtro_tipo"] = "Todos"

    if st.session_state["filtro_arquivo_unico"] not in opcoes_arquivos:
        st.session_state["filtro_arquivo_unico"] = "Todos"

    # Layout dos filtros
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        banco = st.selectbox(
            "Banco de origem",
            options=opcoes_bancos,
            key="filtro_banco"
        )

    with col2:
        if coluna_data and periodo_padrao:
            periodo = st.date_input(
                "Período",
                key="filtro_periodo"
            )
        else:
            periodo = None
            st.selectbox(
                "Período",
                options=["Não disponível"],
                disabled=True
            )

    with col3:
        tipo = st.selectbox(
            "Tipo de lançamento",
            options=opcoes_tipos,
            key="filtro_tipo"
        )

    with col4:
        arquivo = st.selectbox(
            "Arquivo de origem",
            options=opcoes_arquivos,
            key="filtro_arquivo_unico"
        )

    # Botão para limpar os filtros
    st.button(
        "🧹 Limpar filtros",
        on_click=limpar_filtros,
        args=(periodo_padrao,)
    )

    # Aplica os filtros
    df_filtrado = aplicar_filtros(
        df=df,
        banco=banco,
        periodo=periodo,
        tipo=tipo,
        arquivo=arquivo,
        coluna_data=coluna_data,
        coluna_tipo=coluna_tipo
    )

    return df_filtrado
