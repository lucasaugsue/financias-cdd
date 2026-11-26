
import pandas as pd
import streamlit as st

from api.extratos import (
    listar_extratos,
    buscar_movimentacoes,
    atualizar_extrato,
    excluir_extrato,
)

from front.components.importar_extrato import (
    dialog_importar_extrato,
)


@st.dialog("Gerenciar extrato", width="large")
def dialog_gerenciar_extrato(
    extrato_id,
    nome_arquivo,
    banco_origem,
    usuario_id,
):

    st.write(f"**Arquivo:** {nome_arquivo}")
    st.write(f"**Banco:** {banco_origem}")

    try:
        df_movimentacoes = buscar_movimentacoes(
            extrato_id,
            usuario_id,
        )

        st.write(
            f"**Movimentações:** {len(df_movimentacoes)}"
        )

        df_editado = st.data_editor(
            df_movimentacoes,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            key=f"editor_{usuario_id}_{extrato_id}",
        )

        st.divider()

        col_salvar, col_excluir = st.columns(2)

        with col_salvar:

            if st.button(
                "💾 Salvar alterações",
                type="primary",
                width="stretch",
                key=f"salvar_extrato_{usuario_id}_{extrato_id}",
            ):

                try:
                    atualizar_extrato(
                        extrato_id,
                        df_editado,
                        usuario_id,
                    )

                    st.success(
                        "Alterações salvas com sucesso!"
                    )

                    st.rerun()

                except Exception as erro:
                    st.error(
                        f"Erro ao atualizar: {erro}"
                    )

        with col_excluir:

            confirmar = st.checkbox(
                "Confirmar exclusão",
                key=f"confirmar_exclusao_{usuario_id}_{extrato_id}",
            )

            if st.button(
                "🗑️ Excluir extrato",
                disabled=not confirmar,
                width="stretch",
                key=f"excluir_extrato_{usuario_id}_{extrato_id}",
            ):

                try:
                    excluir_extrato(
                        extrato_id,
                        usuario_id,
                    )

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
            f"Não foi possível consultar as movimentações: {erro}"
        )


def render_extratos_salvos():

    usuario_id = st.session_state["usuario"]["id"]

    col_titulo, col_botao = st.columns([3, 1])

    with col_titulo:
        st.subheader("Meus extratos")

    with col_botao:

        if st.button(
            "📥 Importar extrato",
            type="primary",
            width="stretch",
            key="botao_importar_extrato",
        ):
            dialog_importar_extrato()

    try:
        extratos = listar_extratos(usuario_id)

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

        evento = st.dataframe(
            df_extratos,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"tabela_extratos_{usuario_id}",
        )

        linhas_selecionadas = evento.selection.rows

        if linhas_selecionadas:

            indice = linhas_selecionadas[0]
            extrato = extratos[indice]

            dialog_gerenciar_extrato(
                extrato["id"],
                extrato["nome_arquivo"],
                extrato["banco_origem"],
                usuario_id,
            )

    except Exception as erro:
        st.error(
            f"Não foi possível consultar os extratos: {erro}"
        )
