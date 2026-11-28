
import pandas as pd
import streamlit as st

from api.categorias import (
    cadastrar_regra_categorizacao,
    verificar_regra_categorizacao,
    cadastrar_categoria,
)

from api.extratos import (
    atualizar_categoria_manual,
    atualizar_categorias_movimentacoes,
)

from front.components.cache import (
    carregar_categorias,
    carregar_movimentacoes_pendentes,
    carregar_indicadores,
    limpar_cache_categorias,
)

from services.movimentacoes import (
    obter_campo,
    formatar_texto,
    preparar_tabela_movimentacoes,
)

from services.agrupamento import (
    agrupar_movimentacoes_similares,
)


def limpar_selecao_movimentacoes():

    usuario_id = st.session_state.get(
        "usuario_id_dialog_classificacao"
    )

    if usuario_id is None:
        return

    chave_versao = f"versao_tabela_pendentes_{usuario_id}"

    st.session_state[chave_versao] = (
        st.session_state.get(chave_versao, 0) + 1
    )

    st.session_state.pop(
        "usuario_id_dialog_classificacao",
        None,
    )


@st.dialog("Criar nova categoria")
def dialog_nova_categoria(usuario_id):

    with st.form(f"form_nova_categoria_{usuario_id}"):

        nome = st.text_input(
            "Nome da categoria",
            placeholder="Ex.: Pets, Academia, Viagens..."
        )

        finalidade = st.selectbox(
            "Finalidade",
            options=["Despesa", "Receita", "Ambas"],
        )

        salvar = st.form_submit_button(
            "Criar categoria",
            type="primary",
            width="stretch",
        )

        if salvar:

            resultado = cadastrar_categoria(
                nome,
                finalidade,
                usuario_id,
            )

            if resultado == "invalida":
                st.warning("Informe um nome válido para a categoria.")

            elif resultado == "existente":
                st.warning("Essa categoria já está cadastrada.")

            else:
                limpar_cache_categorias()

                st.session_state[
                    f"categoria_movimentacao_pendente_{usuario_id}"
                ] = nome.strip()

                st.success("Categoria criada com sucesso!")

                st.rerun()


@st.dialog(
    "Classificar movimentação",
    on_dismiss=limpar_selecao_movimentacoes,
)
def render_painel_classificacao(linha, categorias, usuario_id):

    detalhes = obter_campo(
        linha,
        ["Detalhes", "detalhes"],
    )

    lancamento = obter_campo(
        linha,
        ["Lançamento", "Lancamento", "lancamento"],
    )

    data = obter_campo(
        linha,
        ["Data", "data"],
    )

    valor = obter_campo(
        linha,
        ["Valor", "valor"],
    )

    tipo = obter_campo(
        linha,
        ["Tipo", "tipo"],
    )

    banco = obter_campo(
        linha,
        ["Banco", "banco", "banco_origem"],
    )

    st.markdown("**Informações da movimentação**")
    st.markdown(f"### {formatar_texto(detalhes)}")

    if lancamento is not None and not pd.isna(lancamento):
        st.caption(formatar_texto(lancamento))

    col_data, col_valor, col_tipo = st.columns(3)

    with col_data:
        st.caption("Data")
        st.write(formatar_texto(data))

    with col_valor:
        st.caption("Valor")
        st.write(formatar_texto(valor))

    with col_tipo:
        st.caption("Tipo")
        st.write(formatar_texto(tipo))

    st.caption(f"Banco: {formatar_texto(banco)}")

    st.divider()

    st.markdown("**Classificação**")

    if st.button(
        "+ Nova categoria",
        key=f"nova_categoria_pendente_{usuario_id}",
    ):
        st.session_state["abrir_dialog_nova_categoria"] = True
        st.rerun()

    opcoes_categorias = {
        categoria["categoria"]: categoria["id"]
        for categoria in categorias
    }

    categoria_atual = st.session_state.get(
        f"categoria_movimentacao_pendente_{usuario_id}"
    )

    indice_categoria = (
        list(opcoes_categorias.keys()).index(categoria_atual)
        if categoria_atual in opcoes_categorias
        else 0
    )

    categoria_escolhida = st.selectbox(
        "Selecione uma categoria",
        options=list(opcoes_categorias.keys()),
        index=indice_categoria,
        key=f"categoria_movimentacao_pendente_{usuario_id}",
    )

    categoria_id = opcoes_categorias[categoria_escolhida]

    cadastrar_palavra = st.checkbox(
        "Cadastrar palavra-chave para futuras movimentações",
        key=f"cadastrar_palavra_movimentacao_{usuario_id}",
    )

    movimentacao_id = obter_campo(
        linha,
        ["movimentacao_id", "id"],
    )

    palavra_chave = ""

    if cadastrar_palavra:
        palavra_chave = st.text_input(
            "Palavra-chave",
            placeholder="Ex.: MERCADO, UBER, FARMACIA...",
            key=f"palavra_chave_movimentacao_{usuario_id}_{movimentacao_id}",
        )

    if st.button(
        "Salvar classificação",
        type="primary",
        width="stretch",
        key=f"salvar_classificacao_movimentacao_{usuario_id}",
    ):

        if cadastrar_palavra:

            resultado = verificar_regra_categorizacao(
                palavra_chave,
                categoria_id,
                usuario_id,
            )

            if resultado == "invalida":
                st.warning("Informe uma palavra-chave válida.")
                return

            if resultado == "conflito":
                st.warning(
                    "Essa palavra-chave já está vinculada "
                    "a outra categoria."
                )
                return

            if resultado == "existente":
                st.warning(
                    "Essa palavra-chave já está cadastrada "
                    "nesta categoria."
                )
                return

        sucesso = atualizar_categoria_manual(
            movimentacao_id,
            categoria_id,
            usuario_id,
        )

        if not sucesso:
            st.error("Não foi possível salvar a classificação.")
            return

        if cadastrar_palavra:
            cadastrar_regra_categorizacao(
                palavra_chave,
                categoria_id,
                usuario_id,
            )

        limpar_cache_categorias()

        limpar_selecao_movimentacoes()

        st.success("Movimentação classificada com sucesso!")

        st.rerun()


@st.fragment
def _render_tabela_movimentacoes_pendentes(
    categorias,
    movimentacoes,
    df_movimentacoes,
    usuario_id,
):

    if movimentacoes.empty:

        st.success("Todas as movimentações estão classificadas!")
        return

    if not categorias:

        st.warning(
            "Cadastre pelo menos uma categoria antes "
            "de classificar as movimentações."
        )
        return

    versao_tabela = st.session_state.get(
        f"versao_tabela_pendentes_{usuario_id}",
        0,
    )

    chave_tabela = (
        f"tabela_movimentacoes_pendentes_{usuario_id}_{versao_tabela}"
    )

    st.info("Selecione uma movimentação para classificar.")

    evento = st.dataframe(
        df_movimentacoes,
        hide_index=True,
        width="stretch",
        height=300,
        on_select="rerun",
        selection_mode="single-row",
        key=chave_tabela,
    )

    linhas_selecionadas = evento.selection.rows

    if linhas_selecionadas:

        indice = linhas_selecionadas[0]

        if indice < len(movimentacoes):

            linha_original = movimentacoes.iloc[indice]

            linha = df_movimentacoes.iloc[indice].copy()

            linha["movimentacao_id"] = obter_campo(
                linha_original,
                ["movimentacao_id", "id"],
            )

            st.session_state[
                "usuario_id_dialog_classificacao"
            ] = usuario_id

            render_painel_classificacao(
                linha,
                categorias,
                usuario_id,
            )

        else:

            st.info(
                "A lista de movimentações foi atualizada. "
                "Selecione novamente uma movimentação."
            )



def _render_teste_agrupamento(
    movimentacoes,
    categorias,
    usuario_id,
):
    grupos = agrupar_movimentacoes_similares(movimentacoes)

    if not grupos:
        st.info(
            "Nenhum grupo de movimentações semelhantes encontrado."
        )
        return

    opcoes_categorias = {
        categoria["categoria"]: categoria["id"]
        for categoria in categorias
    }

    if not opcoes_categorias:
        st.warning("Cadastre pelo menos uma categoria.")
        return

    for numero, grupo in enumerate(grupos, start=1):

        movimentacoes_grupo = grupo["movimentacoes"]

        descricao = grupo["descricao"]
        quantidade = len(movimentacoes_grupo)

        with st.expander(
            f"**{descricao}** — {quantidade} movimentações"
        ):

            st.markdown("**Movimentações deste grupo**")

            for movimentacao in movimentacoes_grupo:

                detalhes = movimentacao.get("Detalhes", "")
                valor = movimentacao.get("Valor", 0)

                try:
                    valor_formatado = float(valor)
                except (TypeError, ValueError):
                    valor_formatado = 0

                sinal = "+" if valor_formatado > 0 else ""

                valor_exibicao = (
                    f"{sinal}R$ {valor_formatado:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

                st.write(
                    f"- {detalhes} | {valor_exibicao}"
                )

            st.divider()

            categoria_escolhida = st.selectbox(
                "Categoria para todas as movimentações",
                options=list(opcoes_categorias.keys()),
                key=f"categoria_grupo_{usuario_id}_{numero}",
            )

            categoria_id = opcoes_categorias[categoria_escolhida]

            if st.button(
                "Classificar todas",
                type="primary",
                key=f"classificar_grupo_{usuario_id}_{numero}",
                width="stretch",
            ):

                df_atualizacao = pd.DataFrame([
                    {
                        "movimentacao_id": movimentacao["movimentacao_id"],
                        "categoria_id": categoria_id,
                    }
                    for movimentacao in movimentacoes_grupo
                ])

                quantidade_atualizada = atualizar_categorias_movimentacoes(
                    df_atualizacao,
                    usuario_id,
                )

                limpar_cache_categorias()

                limpar_selecao_movimentacoes()

                if quantidade_atualizada > 0:
                    st.success(
                        f"{quantidade_atualizada} movimentações "
                        "classificadas com sucesso!"
                    )
                else:
                    st.warning(
                        "Nenhuma movimentação foi atualizada. "
                        "Elas podem já ter sido classificadas."
                    )

                st.rerun()


def render_movimentacoes_pendentes():

    usuario_id = st.session_state["usuario"]["id"]

    st.subheader("Movimentações pendentes")

    st.caption(
        "Classifique as movimentações que ainda não possuem "
        "uma categoria definida."
    )

    try:

        categorias = carregar_categorias(usuario_id)

        movimentacoes = carregar_movimentacoes_pendentes(usuario_id)

        indicadores = carregar_indicadores(usuario_id)

        total_categorizadas = indicadores["categorizadas"]
        total_pendentes = indicadores["pendentes"]

        col_pendentes, col_categorizadas = st.columns(2)

        with col_pendentes:
            st.metric(
                "Movimentações pendentes",
                total_pendentes,
            )

        with col_categorizadas:
            st.metric(
                "Movimentações categorizadas",
                total_categorizadas,
            )

        st.divider()

        if st.session_state.pop("abrir_dialog_nova_categoria", False):
            dialog_nova_categoria(usuario_id)
            return

        if movimentacoes is None or movimentacoes.empty:

            st.success(
                "Todas as movimentações estão classificadas!"
            )
            return

        df_movimentacoes = preparar_tabela_movimentacoes(
            movimentacoes
        )

        # ==========================================
        # CLASSIFICAÇÃO UNITÁRIA
        # ==========================================

        st.subheader("1. Classificação unitária")

        st.caption(
            "Classifique individualmente cada movimentação pendente."
        )

        _render_tabela_movimentacoes_pendentes(
            categorias,
            movimentacoes,
            df_movimentacoes,
            usuario_id,
        )

        st.divider()

        # ==========================================
        # CLASSIFICAÇÃO POR GRUPOS
        # ==========================================

        st.subheader("2. Classificação por grupos")

        st.caption(
            "Encontre movimentações com descrições iguais ou "
            "semelhantes e classifique várias de uma só vez."
        )

        _render_teste_agrupamento(
            movimentacoes,
            categorias,
            usuario_id,
        )

    except Exception as erro:

        st.error(
            f"Erro ao carregar movimentações pendentes: {erro}"
        )
