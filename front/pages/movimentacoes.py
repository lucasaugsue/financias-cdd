
import streamlit as st

from api.extratos import listar_movimentacoes_consolidadas
from front.components.filtros import render_filtros
from services.movimentacoes import preparar_movimentacoes
from front.components.indicadores import render_indicadores


def render_movimentacoes():

    st.subheader("Todas as movimentações")

    try:
        # Consulta e preparação dos dados
        with st.spinner("Carregando movimentações..."):

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

        # Filtros
        df_filtrado = render_filtros(df_consolidado, coluna_data, coluna_tipo)

        st.divider()

        # Indicadores financeiros
        render_indicadores(df_filtrado, coluna_tipo)

        st.divider()

        # Verifica se existem movimentações para apresentar
        if df_filtrado.empty:

            arquivos_selecionados = st.session_state.get(
                "filtro_arquivo", []
            )

            if not arquivos_selecionados:
                st.info(
                    "Nenhum arquivo de origem selecionado. "
                    "Selecione pelo menos um arquivo para visualizar "
                    "as movimentações."
                )
            else:
                st.info(
                    "Nenhuma movimentação encontrada para os filtros selecionados."
                )

            return

        # Tabela de movimentações
        st.dataframe(
            df_filtrado,
            width="stretch",
            hide_index=True,
        )

    except Exception as erro:
        st.error(
            f"Erro ao consultar movimentações: {erro}"
        )
