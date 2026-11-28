
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

from services.movimentacoes import (
    categorizar_movimentacoes,
    padronizar_movimentacoes,
)

def limpar_selecao_extratos():

    usuario_id = st.session_state.get(
        "usuario_id_dialog_extrato"
    )

    if usuario_id is None:
        return

    chave_versao = f"versao_tabela_extratos_{usuario_id}"

    st.session_state[chave_versao] = (
        st.session_state.get(chave_versao, 0) + 1
    )

    st.session_state.pop(
        "usuario_id_dialog_extrato",
        None,
    )


@st.dialog(
    "Gerenciar extrato",
    width="large",
    on_dismiss=limpar_selecao_extratos,
)
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

        # Preserva os IDs das categorias já salvas
        categorias_salvas = df_movimentacoes[
            "categoria_id"
        ].copy()

        # Padroniza os dados antigos para o formato atual
        df_movimentacoes = padronizar_movimentacoes(
            df_movimentacoes
        )

        # Recupera os IDs das categorias após a padronização
        df_movimentacoes["categoria_id"] = (
            categorias_salvas.values
        )

        st.write(
            f"**Movimentações:** {len(df_movimentacoes)}"
        )

        # Identifica o banco nas movimentações
        df_movimentacoes["Banco"] = banco_origem

        # Aplica a categorização automática
        df_movimentacoes = categorizar_movimentacoes(
            df_movimentacoes,
            usuario_id,
        )

        # Organiza as oito colunas da tabela
        colunas_visualizacao = [
            "Data",
            "Valor",
            "Lançamento",
            "Detalhes",
            "Fluxo",
            "Identificador",
            "Banco",
            "categoria",
        ]

        df_visualizacao = df_movimentacoes.reindex(
            columns=colunas_visualizacao
        ).rename(
            columns={
                "categoria": "Categoria",
            }
        )

        df_editado = st.data_editor(
            df_visualizacao,
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

                    limpar_selecao_extratos()

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

                    limpar_selecao_extratos()

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

        # Formata a data de criação no padrão brasileiro
        df_extratos["criado_em"] = pd.to_datetime(
            df_extratos["criado_em"],
            errors="coerce",
        )

        df_extratos["criado_em"] = (
            df_extratos["criado_em"].dt.strftime("%d/%m/%Y às %H:%M")
        )

        # Renomeia as colunas para exibição
        df_extratos = df_extratos.rename(
            columns={
                "id": "ID",
                "nome_arquivo": "Nome do Arquivo",
                "banco_origem": "Banco",
                "quantidade_registros": "Registros",
                "criado_em": "Criado em",
            }
        )

        versao_tabela = st.session_state.get(
            f"versao_tabela_extratos_{usuario_id}",
            0,
        )

        chave_tabela = (
            f"tabela_extratos_{usuario_id}_{versao_tabela}"
        )

        evento = st.dataframe(
            df_extratos,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=chave_tabela,
        )

        linhas_selecionadas = evento.selection.rows

        if linhas_selecionadas:

            indice = linhas_selecionadas[0]
            extrato = extratos[indice]

            st.session_state[
                "usuario_id_dialog_extrato"
            ] = usuario_id

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
