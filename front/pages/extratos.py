
import pandas as pd
import streamlit as st

from api.extratos import (
    listar_extratos,
    buscar_movimentacoes,
    atualizar_extrato,
    excluir_extrato,
)


def render_extratos_salvos():

    st.subheader("Meus extratos")

    try:
        extratos = listar_extratos()

        if not extratos:
            st.info(
                "Você ainda não possui extratos salvos."
            )
            return

        st.metric(
            "Total de extratos",
            len(extratos),
        )

        df_extratos = pd.DataFrame(extratos)

        st.dataframe(
            df_extratos,
            width="stretch",
            hide_index=True,
        )

        st.divider()

        st.subheader("Consultar e editar extrato")

        opcoes = {
            (
                f"{item['nome_arquivo']} - "
                f"{item['banco_origem']} "
                f"(ID: {item['id']})"
            ): item["id"]
            for item in extratos
        }

        selecionado = st.selectbox(
            "Selecione um extrato",
            options=list(opcoes.keys()),
        )

        extrato_id = opcoes[selecionado]

        df_movimentacoes = buscar_movimentacoes(
            extrato_id
        )

        st.write(
            f"**Movimentações:** {len(df_movimentacoes)}"
        )

        df_editado = st.data_editor(
            df_movimentacoes,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            key=f"editor_{extrato_id}",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Salvar alterações",
                type="primary",
                width="stretch"
            ):

                try:
                    atualizar_extrato(
                        extrato_id,
                        df_editado,
                    )

                    st.success(
                        "Alterações salvas com sucesso!"
                    )

                    st.rerun()

                except Exception as erro:
                    st.error(
                        f"Erro ao atualizar: {erro}"
                    )

        with col2:

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este extrato",
                key=f"confirmar_exclusao_{extrato_id}",
            )

            if st.button(
                "🗑️ Excluir extrato",
                disabled=not confirmar,
                width="stretch"
            ):

                try:
                    excluir_extrato(extrato_id)

                    st.success(
                        "Extrato excluído com sucesso!"
                    )

                    st.rerun()

                except Exception as erro:
                    st.error(
                        f"Erro ao excluir: {erro}"
                    )

    except Exception as erro:
        st.error(
            f"Não foi possível consultar os extratos: {erro}"
        )
