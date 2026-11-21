
import pandas as pd
import streamlit as st

from api.categorias import (
    listar_categorias,
    listar_regras_categorizacao,
    cadastrar_regra_categorizacao,
    editar_regra_categorizacao,
    excluir_regra_categorizacao,
    verificar_regra_categorizacao,
)

from api.extratos import (
    listar_movimentacoes_pendentes,
    contar_movimentacoes_categorizadas,
    atualizar_categoria_manual,
)


def obter_campo(linha, nomes):
    """Localiza uma coluna considerando possíveis variações no nome."""

    for coluna in linha.index:
        if str(coluna).strip().casefold() in [
            nome.casefold() for nome in nomes
        ]:
            return linha[coluna]

    return None


def formatar_texto(valor):
    """Prepara valores para exibição."""

    if valor is None or pd.isna(valor):
        return "—"

    return str(valor)


def render_categorias():

    st.subheader("Gerenciar categorias")

    try:
        categorias = listar_categorias()
        regras = listar_regras_categorizacao()

        movimentacoes = listar_movimentacoes_pendentes()
        indicadores = contar_movimentacoes_categorizadas()

        # Agrupar palavras-chave por categoria
        palavras_por_categoria = {}

        for regra in regras:
            categoria_id = regra["categoria_id"]

            if categoria_id not in palavras_por_categoria:
                palavras_por_categoria[categoria_id] = []

            palavras_por_categoria[categoria_id].append(
                regra["palavra_chave"]
            )

        # Indicadores
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.metric(
                    label="Categorias cadastradas",
                    value=len(categorias),
                    help="Quantidade total de categorias disponíveis."
                )

        with col2:
            with st.container(border=True):
                st.metric(
                    label="Palavras-chave cadastradas",
                    value=len(regras),
                    help="Quantidade de regras de categorização ativas."
                )

        with col3:
            with st.container(border=True):
                st.metric(
                    label="Movimentações pendentes",
                    value=indicadores["pendentes"],
                    help="Quantidade de movimentações sem categoria."
                )

        with col4:
            with st.container(border=True):
                st.metric(
                    label="Movimentações categorizadas",
                    value=indicadores["categorizadas"],
                    help="Quantidade de movimentações com categoria."
                )

        st.divider()

        
        # Categorias e palavras-chave
        st.subheader("Categorias e palavras-chave")

        # Contabilizar palavras por categoria
        quantidade_palavras = {}

        for regra in regras:
            categoria_id = regra["categoria_id"]

            quantidade_palavras[categoria_id] = (
                quantidade_palavras.get(categoria_id, 0) + 1
            )

        # Ordenar da categoria com mais palavras para a com menos
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

        # Garantir que a página atual continue válida
        st.session_state.pagina_categorias = min(
            st.session_state.pagina_categorias,
            total_paginas - 1,
        )

        inicio = (
            st.session_state.pagina_categorias * itens_por_pagina
        )

        fim = inicio + itens_por_pagina

        categorias_pagina = categorias_ordenadas[inicio:fim]

        # Modais de gerenciamento
        @st.dialog("Adicionar palavra-chave")
        def dialog_adicionar(categoria_id, nome_categoria):

            st.caption(f"Categoria: {nome_categoria}")

            with st.form("form_modal_adicionar"):

                nova_palavra = st.text_input(
                    "Palavra-chave"
                )

                confirmar = st.form_submit_button(
                    "Adicionar",
                    use_container_width=True,
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
                            st.success("Palavra-chave cadastrada!")
                            st.rerun()
                        else:
                            st.warning(
                                "Essa palavra já existe nesta categoria."
                            )

        @st.dialog("Editar palavra-chave")
        def dialog_editar(regra_id, palavra_atual):

            with st.form("form_modal_editar"):

                palavra_editada = st.text_input(
                    "Palavra-chave",
                    value=palavra_atual,
                )

                confirmar = st.form_submit_button(
                    "Salvar alteração",
                    use_container_width=True,
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
                            st.success("Palavra-chave atualizada!")
                            st.rerun()
                        else:
                            st.warning(
                                "Não foi possível atualizar. "
                                "Verifique se a palavra já existe."
                            )

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
                    use_container_width=True,
                ):
                    st.rerun()

            with col2:
                if st.button(
                    "Confirmar exclusão",
                    type="primary",
                    use_container_width=True,
                ):

                    sucesso = excluir_regra_categorizacao(regra_id)

                    if sucesso:
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

                # Identificador da tabela
                chave_tabela = f"tabela_palavras_{categoria_id}"

                # Preparar dados da tabela
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

                # Identificar linha selecionada
                if palavras:
                    evento = st.dataframe(
                        df_palavras,
                        hide_index=True,
                        use_container_width=True,
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

                # Botões de gerenciamento
                col_adicionar, col_editar, col_excluir = st.columns(3)

                with col_adicionar:
                    if st.button(
                        "＋ Adicionar",
                        key=f"adicionar_{categoria_id}",
                        use_container_width=True,
                    ):
                        dialog_adicionar(categoria_id, nome)

                with col_editar:
                    if st.button(
                        "✏️ Editar",
                        key=f"editar_{categoria_id}",
                        disabled=regra_selecionada is None,
                        use_container_width=True,
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
                        use_container_width=True,
                    ):
                        dialog_excluir(
                            regra_selecionada["id"],
                            regra_selecionada["palavra_chave"],
                        )

                if not palavras:
                    st.info("Nenhuma palavra-chave cadastrada.")

        # Controles de paginação
        st.divider()

        col_anterior, col_pagina, col_proxima = st.columns(
            [1, 2, 1]
        )

        with col_anterior:
            if st.button(
                "← Anterior",
                disabled=st.session_state.pagina_categorias == 0,
                use_container_width=True,
            ):
                st.session_state.pagina_categorias -= 1
                st.rerun()

        with col_pagina:
            st.markdown(
                f"<center>Página "
                f"{st.session_state.pagina_categorias + 1} "
                f"de {total_paginas}</center>",
                unsafe_allow_html=True,
            )

        with col_proxima:
            if st.button(
                "Próxima →",
                disabled=(
                    st.session_state.pagina_categorias
                    >= total_paginas - 1
                ),
                use_container_width=True,
            ):
                st.session_state.pagina_categorias += 1
                st.rerun()

        st.divider()
        
        # Movimentações pendentes
        st.subheader("Movimentações pendentes")

        st.caption(
            "Selecione uma movimentação na tabela para classificá-la."
        )

        if movimentacoes.empty:
            st.success("Todas as movimentações estão categorizadas!")

        elif not categorias:
            st.warning(
                "Cadastre pelo menos uma categoria antes de "
                "classificar as movimentações."
            )

        else:
            opcoes_categorias = {
                categoria["categoria"]: categoria["id"]
                for categoria in categorias
            }

            # Preparar dados da tabela
            dados_tabela = []
            linhas_originais = []

            for _, linha in movimentacoes.iterrows():

                linhas_originais.append(linha)

                dados_tabela.append({
                    "Data": formatar_texto(
                        obter_campo(linha, ["Data", "Date"])
                    ),
                    "Detalhes": formatar_texto(
                        obter_campo(linha, ["Detalhes"])
                    ),
                    "Lançamento": formatar_texto(
                        obter_campo(linha, ["Lançamento"])
                    ),
                    "Valor": formatar_texto(
                        obter_campo(linha, ["BRL", "Valor"])
                    ),
                    "Tipo": formatar_texto(
                        obter_campo(linha, ["Tipo Lançamento"])
                    ),
                    "Banco": formatar_texto(
                        linha.get("banco_origem")
                    ),
                })

            df_movimentacoes = pd.DataFrame(dados_tabela)

            # Tabela de movimentações
            evento = st.dataframe(
                df_movimentacoes,
                hide_index=True,
                use_container_width=True,
                height=300,
                on_select="rerun",
                selection_mode="single-row",
                key="tabela_movimentacoes_pendentes",
            )

            linhas_selecionadas = evento.selection.rows

            # Recuperar movimentação selecionada
            if linhas_selecionadas:

                indice = linhas_selecionadas[0]
                linha = linhas_originais[indice]

                movimentacao_id = int(linha["movimentacao_id"])

                data = formatar_texto(
                    obter_campo(linha, ["Data", "Date"])
                )

                detalhes = formatar_texto(
                    obter_campo(linha, ["Detalhes"])
                )

                lancamento = formatar_texto(
                    obter_campo(linha, ["Lançamento"])
                )

                valor = formatar_texto(
                    obter_campo(linha, ["BRL", "Valor"])
                )

                tipo = formatar_texto(
                    obter_campo(linha, ["Tipo Lançamento"])
                )

                banco = formatar_texto(
                    linha.get("banco_origem")
                )

                st.divider()

                # Painel de classificação
                st.subheader("Classificar movimentação")

                with st.container(border=True):

                    st.markdown(f"**{detalhes}**")

                    if lancamento != "—":
                        st.caption(f"Lançamento: {lancamento}")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.caption("Data")
                        st.write(data)

                    with col2:
                        st.caption("Valor")
                        st.write(f"**{valor}**")

                    with col3:
                        st.caption("Tipo")
                        st.write(tipo)

                    st.caption(f"Banco: {banco}")

                    st.divider()

                    categoria_escolhida = st.selectbox(
                        "Categoria",
                        options=list(opcoes_categorias.keys()),
                        key=f"categoria_{movimentacao_id}",
                    )

                    cadastrar_palavra = st.checkbox(
                        "Cadastrar palavra-chave para esta categoria",
                        key=f"cadastrar_palavra_{movimentacao_id}",
                    )

                    palavra_chave = ""

                    if cadastrar_palavra:
                        palavra_chave = st.text_input(
                            "Palavra-chave",
                            value=(
                                detalhes if detalhes != "—" else ""
                            ),
                            key=f"palavra_chave_{movimentacao_id}",
                            help=(
                                "Informe o texto que será utilizado "
                                "para identificar outras movimentações."
                            ),
                        )

                    
                    if st.button(
                        "Salvar classificação",
                        type="primary",
                        use_container_width=True,
                        key=f"salvar_categoria_{movimentacao_id}",
                    ):

                        categoria_id = opcoes_categorias[
                            categoria_escolhida
                        ]

                        # Verificar palavra-chave, se solicitado
                        status_regra = None

                        if cadastrar_palavra:

                            if not palavra_chave.strip():
                                st.warning(
                                    "Informe uma palavra-chave."
                                )
                                st.stop()

                            status_regra = verificar_regra_categorizacao(
                                palavra_chave,
                                categoria_id,
                            )

                            if status_regra["status"] == "invalida":
                                st.warning(
                                    "Informe uma palavra-chave válida."
                                )
                                st.stop()

                        # Salvar classificação manual
                        sucesso = atualizar_categoria_manual(
                            movimentacao_id,
                            categoria_id,
                        )

                        if sucesso:

                            # Cadastrar nova regra, se necessário
                            if cadastrar_palavra:

                                if status_regra["status"] == "conflito":

                                    categorias_conflito = ", ".join(
                                        status_regra["categorias"]
                                    )

                                    st.warning(
                                        "Classificação salva, mas a "
                                        "palavra-chave não foi cadastrada. "
                                        f"Ela já pertence à categoria: "
                                        f"{categorias_conflito}."
                                    )

                                elif status_regra["status"] == "existente":

                                    st.success(
                                        "Classificação salva! "
                                        "Essa palavra-chave já estava "
                                        "cadastrada nesta categoria."
                                    )

                                else:
                                    regra_criada = (
                                        cadastrar_regra_categorizacao(
                                            palavra_chave,
                                            categoria_id,
                                        )
                                    )

                                    if regra_criada:
                                        st.success(
                                            "Classificação salva e "
                                            "palavra-chave cadastrada!"
                                        )
                                    else:
                                        st.warning(
                                            "Classificação salva, mas "
                                            "não foi possível cadastrar "
                                            "a palavra-chave."
                                        )

                            else:
                                st.success(
                                    "Categoria salva com sucesso!"
                                )

                            st.rerun()

                        else:
                            st.error(
                                "Não foi possível atualizar "
                                "a movimentação."
                            )

                    #termina aqui
            else:
                st.info(
                    "Selecione uma movimentação na tabela "
                    "para visualizar os detalhes e classificá-la."
                )

    except Exception as erro:
        st.error(f"Erro ao carregar categorias: {erro}")
