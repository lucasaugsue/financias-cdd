
import pandas as pd
import streamlit as st

from api.categorias import (
    listar_categorias,
    listar_regras_categorizacao,
    cadastrar_regra_categorizacao,
    editar_regra_categorizacao,
    excluir_regra_categorizacao,
)

from front.components.cache import (
    carregar_categorias,
    carregar_regras,
    limpar_cache_categorias,
)


@st.fragment
def render_lista_categorias(categorias, regras):

    st.subheader("Categorias e palavras-chave")

    # Contabilizar palavras por categoria
    quantidade_palavras = {}

    for regra in regras:
        categoria_id = regra["categoria_id"]
        quantidade_palavras[categoria_id] = (
            quantidade_palavras.get(categoria_id, 0) + 1
        )

    # Ordenar categorias
    categorias_ordenadas = sorted(
        categorias,
        key=lambda categoria: (
            -quantidade_palavras.get(categoria["id"], 0),
            categoria["categoria"].casefold(),
        ),
    )

    # Paginação
    itens_por_pagina = 10

    total_paginas = max(
        1,
        (len(categorias_ordenadas) + itens_por_pagina - 1)
        // itens_por_pagina,
    )

    if "pagina_categorias" not in st.session_state:
        st.session_state.pagina_categorias = 0

    st.session_state.pagina_categorias = min(
        st.session_state.pagina_categorias,
        total_paginas - 1,
    )

    inicio = st.session_state.pagina_categorias * itens_por_pagina
    fim = inicio + itens_por_pagina

    categorias_pagina = categorias_ordenadas[inicio:fim]

    # Diálogo: adicionar
    @st.dialog("Adicionar palavra-chave")
    def dialog_adicionar(categoria_id, nome_categoria):

        st.caption(f"Categoria: {nome_categoria}")

        with st.form("form_modal_adicionar"):

            nova_palavra = st.text_input("Palavra-chave")

            confirmar = st.form_submit_button(
                "Adicionar",
                width="stretch",
            )

            if confirmar:
                if not nova_palavra.strip():
                    st.warning("Informe uma palavra-chave.")
                else:
                    sucesso = cadastrar_regra_categorizacao(
                        nova_palavra,
                        categoria_id,
                    )

                    if sucesso:
                        limpar_cache_categorias()
                        st.success("Palavra-chave cadastrada!")
                        st.rerun()
                    else:
                        st.warning(
                            "Essa palavra já existe nesta categoria."
                        )

    # Diálogo: editar
    @st.dialog("Editar palavra-chave")
    def dialog_editar(regra_id, palavra_atual):

        with st.form("form_modal_editar"):

            palavra_editada = st.text_input(
                "Palavra-chave",
                value=palavra_atual,
            )

            confirmar = st.form_submit_button(
                "Salvar alteração",
                width="stretch",
            )

            if confirmar:
                if not palavra_editada.strip():
                    st.warning("Informe uma palavra-chave.")
                else:
                    sucesso = editar_regra_categorizacao(
                        regra_id,
                        palavra_editada,
                    )

                    if sucesso:
                        limpar_cache_categorias()
                        st.success("Palavra-chave atualizada!")
                        st.rerun()
                    else:
                        st.warning(
                            "Não foi possível atualizar. "
                            "Verifique se a palavra já existe."
                        )

    # Diálogo: excluir
    @st.dialog("Excluir palavra-chave")
    def dialog_excluir(regra_id, palavra):

        st.write(
            f"Deseja realmente excluir a palavra-chave "
            f"**{palavra}**?"
        )

        st.warning(
            "Ela deixará de ser utilizada nas próximas "
            "categorizações automáticas."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Cancelar", width="stretch"):
                st.rerun()

        with col2:
            if st.button(
                "Confirmar exclusão",
                type="primary",
                width="stretch",
            ):
                sucesso = excluir_regra_categorizacao(regra_id)

                if sucesso:
                    limpar_cache_categorias()
                    st.success("Palavra-chave excluída!")
                    st.rerun()
                else:
                    st.error("Não foi possível excluir a palavra.")

    # Exibir categorias
    for categoria in categorias_pagina:

        categoria_id = categoria["id"]
        nome = categoria["categoria"]
        finalidade = categoria["finalidade"]

        palavras = [
            regra for regra in regras
            if regra["categoria_id"] == categoria_id
        ]

        with st.expander(
            f"{nome} ({len(palavras)} palavras-chave)"
        ):

            st.caption(f"Finalidade: {finalidade}")

            chave_tabela = f"tabela_palavras_{categoria_id}"

            df_palavras = pd.DataFrame([
                {
                    "ID": regra["id"],
                    "Palavra-chave": regra["palavra_chave"],
                    "Data de criação": pd.to_datetime(
                        regra["criado_em"]
                    ).strftime("%d/%m/%Y"),
                }
                for regra in palavras
            ])

            if palavras:
                evento = st.dataframe(
                    df_palavras,
                    hide_index=True,
                    width="stretch",
                    height=220,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=chave_tabela,
                )

                linhas_selecionadas = evento.selection.rows

                regra_selecionada = (
                    palavras[linhas_selecionadas[0]]
                    if linhas_selecionadas
                    else None
                )
            else:
                regra_selecionada = None

            col_adicionar, col_editar, col_excluir = st.columns(3)

            with col_adicionar:
                if st.button(
                    "＋ Adicionar",
                    key=f"adicionar_{categoria_id}",
                    width="stretch",
                ):
                    dialog_adicionar(categoria_id, nome)

            with col_editar:
                if st.button(
                    "✏️ Editar",
                    key=f"editar_{categoria_id}",
                    disabled=regra_selecionada is None,
                    width="stretch",
                ):
                    dialog_editar(
                        regra_selecionada["id"],
                        regra_selecionada["palavra_chave"],
                    )

            with col_excluir:
                if st.button(
                    "🗑️ Excluir",
                    key=f"excluir_{categoria_id}",
                    disabled=regra_selecionada is None,
                    width="stretch",
                ):
                    dialog_excluir(
                        regra_selecionada["id"],
                        regra_selecionada["palavra_chave"],
                    )

            if not palavras:
                st.info("Nenhuma palavra-chave cadastrada.")

    # Paginação
    st.divider()

    col_anterior, col_pagina, col_proxima = st.columns([1, 2, 1])

    with col_anterior:
        st.button(
            "← Anterior",
            disabled=st.session_state.pagina_categorias == 0,
            width="stretch",
            key="pagina_anterior_categorias",
            on_click=lambda: setattr(
                st.session_state,
                "pagina_categorias",
                st.session_state.pagina_categorias - 1,
            ),
        )

    with col_pagina:
        st.markdown(
            f"<center>Página "
            f"{st.session_state.pagina_categorias + 1} "
            f"de {total_paginas}</center>",
            unsafe_allow_html=True,
        )

    with col_proxima:
        st.button(
            "Próxima →",
            disabled=(
                st.session_state.pagina_categorias >= total_paginas - 1
            ),
            width="stretch",
            key="pagina_proxima_categorias",
            on_click=lambda: setattr(
                st.session_state,
                "pagina_categorias",
                st.session_state.pagina_categorias + 1,
            ),
        )


def render_categorias():

    st.subheader("Gerenciar categorias")

    try:
        categorias = carregar_categorias()
        regras = carregar_regras()

        render_lista_categorias(categorias, regras)

    except Exception as erro:
        st.error(f"Erro ao carregar categorias: {erro}")
