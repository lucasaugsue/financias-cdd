
import pandas as pd
import streamlit as st

from api.regras_padrao import listar_regras_padrao

from api.categorias import (
    cadastrar_regra_categorizacao,
    editar_regra_categorizacao,
    excluir_regra_categorizacao,
    cadastrar_categoria,
)

from front.components.cache import (
    carregar_categorias,
    carregar_regras,
    limpar_cache_categorias,
)


@st.dialog("Nova categoria")
def dialog_nova_categoria(usuario_id):

    with st.form(f"form_nova_categoria_{usuario_id}"):

        nome = st.text_input(
            "Nome da categoria",
            placeholder="Ex.: Academia, Pets, Viagens..."
        )

        finalidade = st.selectbox(
            "Finalidade",
            options=["Despesa", "Receita", "Ambas"],
        )

        confirmar = st.form_submit_button(
            "Criar categoria",
            type="primary",
            width="stretch",
        )

        if confirmar:

            resultado = cadastrar_categoria(
                nome,
                finalidade,
                usuario_id,
            )

            if resultado == "invalida":
                st.warning("Informe um nome válido.")

            elif resultado == "existente":
                st.warning("Essa categoria já está cadastrada.")

            elif resultado == "criada":
                limpar_cache_categorias()
                st.success("Categoria criada com sucesso!")
                st.rerun()


@st.fragment
def render_lista_categorias(
    categorias,
    regras,
    regras_padrao,
    usuario_id,
):

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

    # Paginação individual por usuário
    chave_pagina = f"pagina_categorias_{usuario_id}"

    itens_por_pagina = 10

    total_paginas = max(
        1,
        (len(categorias_ordenadas) + itens_por_pagina - 1)
        // itens_por_pagina,
    )

    if chave_pagina not in st.session_state:
        st.session_state[chave_pagina] = 0

    st.session_state[chave_pagina] = min(
        st.session_state[chave_pagina],
        total_paginas - 1,
    )

    inicio = st.session_state[chave_pagina] * itens_por_pagina
    fim = inicio + itens_por_pagina

    categorias_pagina = categorias_ordenadas[inicio:fim]

    # Diálogo: adicionar
    @st.dialog("Adicionar palavra-chave")
    def dialog_adicionar(categoria_id, nome_categoria):

        st.caption(f"Categoria: {nome_categoria}")

        with st.form(f"form_modal_adicionar_{usuario_id}"):

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
                        usuario_id,
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

        with st.form(f"form_modal_editar_{usuario_id}"):

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
                        usuario_id,
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
            if st.button(
                "Cancelar",
                width="stretch",
                key=f"cancelar_exclusao_{usuario_id}",
            ):
                st.rerun()

        with col2:
            if st.button(
                "Confirmar exclusão",
                type="primary",
                width="stretch",
                key=f"confirmar_exclusao_{usuario_id}",
            ):
                sucesso = excluir_regra_categorizacao(
                    regra_id,
                    usuario_id,
                )

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

        # Separar regras personalizadas e padrão
        palavras_usuario = [
            regra for regra in regras
            if regra["categoria_id"] == categoria_id
        ]

        palavras_padrao = [
            regra for regra in regras_padrao
            if regra["categoria"].casefold() == nome.casefold()
        ]

        total_palavras = len(palavras_usuario) + len(palavras_padrao)

        with st.expander(
            f"{nome} ({total_palavras} palavras-chave)"
        ):

            st.caption(f"Finalidade: {finalidade}")

            # Palavras padrão do sistema
            st.markdown("#### 🔒 Palavras-chave padrão")

            st.caption(
                "Compartilhadas por todos os usuários. "
                "Não podem ser editadas ou excluídas."
            )

            if palavras_padrao:

                df_padrao = pd.DataFrame([
                    {
                        "Palavra-chave": regra["palavra_chave"],
                        "Origem": "Padrão do sistema",
                    }
                    for regra in palavras_padrao
                ])

                st.dataframe(
                    df_padrao,
                    hide_index=True,
                    width="stretch",
                    height=min(220, 40 * len(df_padrao) + 38),
                )

            else:
                st.caption(
                    "Nenhuma palavra-chave padrão nesta categoria."
                )

            st.divider()

            # Palavras personalizadas do usuário
            st.markdown("#### ✏️ Minhas palavras-chave")

            st.caption(
                "Palavras criadas por você. "
                "Podem ser editadas ou excluídas."
            )

            chave_tabela = (
                f"tabela_palavras_{usuario_id}_{categoria_id}"
            )

            df_palavras = pd.DataFrame([
                {
                    "ID": regra["id"],
                    "Palavra-chave": regra["palavra_chave"],
                    "Data de criação": pd.to_datetime(
                        regra["criado_em"]
                    ).strftime("%d/%m/%Y"),
                }
                for regra in palavras_usuario
            ])

            if palavras_usuario:

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
                    palavras_usuario[linhas_selecionadas[0]]
                    if linhas_selecionadas
                    else None
                )

            else:
                regra_selecionada = None

                st.info(
                    "Você ainda não cadastrou palavras "
                    "personalizadas nesta categoria."
                )

            col_adicionar, col_editar, col_excluir = st.columns(3)

            with col_adicionar:

                if st.button(
                    "＋ Adicionar",
                    key=f"adicionar_{usuario_id}_{categoria_id}",
                    width="stretch",
                ):
                    dialog_adicionar(categoria_id, nome)

            with col_editar:

                if st.button(
                    "✏️ Editar",
                    key=f"editar_{usuario_id}_{categoria_id}",
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
                    key=f"excluir_{usuario_id}_{categoria_id}",
                    disabled=regra_selecionada is None,
                    width="stretch",
                ):
                    dialog_excluir(
                        regra_selecionada["id"],
                        regra_selecionada["palavra_chave"],
                    )

    # Paginação
    st.divider()

    col_anterior, col_pagina, col_proxima = st.columns([1, 2, 1])

    with col_anterior:
        st.button(
            "← Anterior",
            disabled=st.session_state[chave_pagina] == 0,
            width="stretch",
            key=f"pagina_anterior_categorias_{usuario_id}",
            on_click=lambda: st.session_state.update({
                chave_pagina: st.session_state[chave_pagina] - 1
            }),
        )

    with col_pagina:
        st.markdown(
            f"<center>Página "
            f"{st.session_state[chave_pagina] + 1} "
            f"de {total_paginas}</center>",
            unsafe_allow_html=True,
        )

    with col_proxima:
        st.button(
            "Próxima →",
            disabled=(
                st.session_state[chave_pagina] >= total_paginas - 1
            ),
            width="stretch",
            key=f"pagina_proxima_categorias_{usuario_id}",
            on_click=lambda: st.session_state.update({
                chave_pagina: st.session_state[chave_pagina] + 1
            }),
        )


def render_categorias():

    usuario_id = st.session_state["usuario"]["id"]

    col_titulo, col_botao = st.columns([3, 1])

    with col_titulo:
        st.subheader("Gerenciar categorias")

    with col_botao:
        if st.button(
            "+ Nova categoria",
            type="primary",
            width="stretch",
            key=f"botao_nova_categoria_{usuario_id}",
        ):
            dialog_nova_categoria(usuario_id)

    try:
        categorias = carregar_categorias(usuario_id)
        regras = carregar_regras(usuario_id)
        regras_padrao = listar_regras_padrao()

        render_lista_categorias(
            categorias,
            regras,
            regras_padrao,
            usuario_id,
        )

    except Exception as erro:
        st.error(f"Erro ao carregar categorias: {erro}")
