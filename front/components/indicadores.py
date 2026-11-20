
import streamlit as st

from services.movimentacoes import calcular_indicadores


def formatar_moeda(valor):
    """Formata um número no padrão monetário brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_indicadores(df, coluna_tipo):
    indicadores = calcular_indicadores(df, coluna_tipo)

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.metric(
                label="Total de movimentações",
                value=f"{indicadores['total_movimentacoes']:,}".replace(",", "."),
                help="Quantidade de movimentações considerando os filtros aplicados."
            )

    with col2:
        with st.container(border=True):
            st.metric(
                label="Total de entradas",
                value=formatar_moeda(indicadores["total_entradas"]),
                help="Soma dos valores das movimentações classificadas como entrada."
            )

    with col3:
        with st.container(border=True):
            st.metric(
                label="Total de saídas",
                value=formatar_moeda(indicadores["total_saidas"]),
                help="Soma dos valores das movimentações classificadas como saída."
            )
