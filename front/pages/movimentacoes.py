
import streamlit as st

from front.components.filtros import render_filtros
from front.components.indicadores import render_indicadores
from api.extratos import (
    listar_movimentacoes_consolidadas,
    atualizar_categorias_movimentacoes,
)
from services.movimentacoes import (
    preparar_movimentacoes,
    converter_valor_monetario,
    categorizar_movimentacoes,
)


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

            # Categorizar movimentações automaticamente
            df_consolidado = categorizar_movimentacoes(df_consolidado)
            atualizar_categorias_movimentacoes(df_consolidado)

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

        # Colunas que não devem aparecer na tabela
        colunas_ocultas = [
            "arquivo_origem",
            "extrato_id",
            "movimentacao_id",
        ]

        # Remove apenas da visualização, sem alterar os dados originais
        df_visualizacao = df_filtrado.rename(
            columns={
                "banco_origem": "Banco",
                "Valor": "BRL",
            }
        ).drop(
            columns=colunas_ocultas,
            errors="ignore"
        )

        # Máscara monetária brasileira, somente para visualização
        if "BRL" in df_visualizacao.columns:
            df_visualizacao["BRL"] = df_visualizacao["BRL"].apply(
                converter_valor_monetario
            ).map(
                lambda valor: f"R$ {valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        
        # Tabela de movimentações
        st.dataframe(
            df_visualizacao,
            width="stretch",
            hide_index=True,
        )

    except Exception as erro:
        st.error(
            f"Erro ao consultar movimentações: {erro}"
        )
