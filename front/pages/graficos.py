
import streamlit as st

from api.extratos import listar_movimentacoes_consolidadas
from services.movimentacoes import preparar_movimentacoes
from front.components.graficos import render_grafico_evolucao


def render_graficos():

    st.subheader("Análise financeira")

    try:
        with st.spinner("Carregando informações financeiras e preparando gráfico..."):

            df_consolidado = listar_movimentacoes_consolidadas()

            if df_consolidado.empty:
                st.info(
                    "Ainda não existem movimentações cadastradas."
                )
                return

            (
                df_consolidado,
                coluna_data,
                coluna_tipo,
            ) = preparar_movimentacoes(df_consolidado)

            render_grafico_evolucao(
                df_consolidado,
                coluna_data,
                coluna_tipo
            )

    except Exception as erro:
        st.error(
            f"Erro ao carregar os gráficos: {erro}"
        )
