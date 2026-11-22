
import streamlit as st

from services.movimentacoes import (
    aplicar_filtros,
    listar_periodos_disponiveis
)


OPCAO_SEM_CATEGORIA = "__SEM_CATEGORIA__"


def limpar_filtros():
    """Restaura os filtros para os valores iniciais."""

    st.session_state["filtro_banco"] = "Todos"
    st.session_state["filtro_tipo"] = "Todos"
    st.session_state["filtro_periodos"] = []
    st.session_state["filtro_categoria"] = "Todos"


def formatar_periodo(periodo):
    """Transforma YYYY-MM em NomeDoMês/AAAA."""

    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    ano, mes = periodo.split("-")

    return f"{meses[int(mes) - 1]}/{ano}"


def render_filtros(df, coluna_data, coluna_tipo):

    # Identifica as opções disponíveis
    bancos = sorted(
        df["banco_origem"].dropna().unique().tolist()
    )

    tipos = []

    if coluna_tipo:
        tipos = sorted(
            df[coluna_tipo].dropna().astype(str).unique().tolist()
        )

    categorias = []

    if "categoria" in df.columns:
        categorias = sorted(
            df["categoria"].dropna().astype(str).unique().tolist()
        )

    periodos = listar_periodos_disponiveis(
        df,
        coluna_data
    )

    # Inicializa os estados
    if "filtro_banco" not in st.session_state:
        st.session_state["filtro_banco"] = "Todos"

    if "filtro_tipo" not in st.session_state:
        st.session_state["filtro_tipo"] = "Todos"

    if "filtro_periodos" not in st.session_state:
        st.session_state["filtro_periodos"] = periodos

    if "filtro_categoria" not in st.session_state:
        st.session_state["filtro_categoria"] = "Todos"

    # Corrige seleções que não existem mais nas opções
    if st.session_state["filtro_banco"] not in ["Todos"] + bancos:
        st.session_state["filtro_banco"] = "Todos"

    if st.session_state["filtro_tipo"] not in ["Todos"] + tipos:
        st.session_state["filtro_tipo"] = "Todos"

    opcoes_categoria = (
        ["Todos", OPCAO_SEM_CATEGORIA] + categorias
    )

    if st.session_state["filtro_categoria"] not in opcoes_categoria:
        st.session_state["filtro_categoria"] = "Todos"

    if not set(st.session_state["filtro_periodos"]).issubset(set(periodos)):
        st.session_state["filtro_periodos"] = periodos

    # Layout dos filtros
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        periodos_selecionados = st.multiselect(
            "Mês/Ano",
            options=periodos,
            format_func=formatar_periodo,
            key="filtro_periodos"
        )

    with col2:
        banco = st.selectbox(
            "Banco de origem",
            options=["Todos"] + bancos,
            key="filtro_banco"
        )

    with col3:
        tipo = st.selectbox(
            "Tipo de lançamento",
            options=["Todos"] + tipos,
            key="filtro_tipo"
        )

    with col4:
        categoria = st.selectbox(
            "Categoria",
            options=opcoes_categoria,
            format_func=lambda opcao: (
                "Sem categoria"
                if opcao == OPCAO_SEM_CATEGORIA
                else opcao
            ),
            key="filtro_categoria"
        )

    # Botão para limpar os filtros
    st.button(
        "🧹 Limpar filtros",
        on_click=limpar_filtros
    )

    # Aplica os filtros existentes
    df_filtrado = aplicar_filtros(
        df=df,
        banco=banco,
        periodos=periodos_selecionados,
        tipo=tipo,
        coluna_data=coluna_data,
        coluna_tipo=coluna_tipo
    )

    # Aplica o filtro de categoria
    if categoria == OPCAO_SEM_CATEGORIA:
        df_filtrado = df_filtrado[
            df_filtrado["categoria"].isna()
        ]

    elif categoria != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["categoria"] == categoria
        ]

    return df_filtrado
