
import streamlit as st

from api.extratos import listar_movimentacoes_consolidadas
from services.movimentacoes import preparar_movimentacoes

from front.components.graficos import (
    render_grafico_categorias,
    render_grafico_evolucao,
)


def render_graficos():

    st.subheader("Análise financeira")

    # Seletor principal
    tipo_grafico = st.selectbox(
        "Selecione o gráfico",
        [
            "Evolução financeira mensal",
            "Análise por categorias",
        ],
        key="seletor_principal_graficos",
    )

    try:
        with st.spinner("Carregando informações financeiras..."):

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

        # Exibe somente a análise selecionada
        if tipo_grafico == "Evolução financeira mensal":

            render_grafico_evolucao(
                df_consolidado,
                coluna_data,
                coluna_tipo
            )

        elif tipo_grafico == "Análise por categorias":

            render_grafico_categorias(df_consolidado)

    except Exception as erro:
        st.error(
            f"Erro ao carregar os gráficos: {erro}"
        )
