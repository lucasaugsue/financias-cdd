
import pandas as pd
import streamlit as st

from api.categorias import (
    cadastrar_regra_categorizacao,
    verificar_regra_categorizacao,
    cadastrar_categoria,
)

from api.extratos import (
    listar_movimentacoes_pendentes,
    contar_movimentacoes_categorizadas,
    atualizar_categoria_manual,
)

from front.components.cache import (
    carregar_categorias,
    carregar_movimentacoes_pendentes,
    carregar_indicadores,
    limpar_cache_categorias,
)


def obter_campo(linha, nomes):

    nomes_normalizados = [
        nome.casefold()
        for nome in nomes
    ]

    for coluna in linha.index:

        if str(coluna).strip().casefold() in nomes_normalizados:
            return linha[coluna]

    return None


def formatar_texto(valor):

    if valor is None or pd.isna(valor):
        return "—"

    return str(valor)


def preparar_tabela_movimentacoes(movimentacoes):

    if movimentacoes is None or movimentacoes.empty:
        return pd.DataFrame()

    registros = []

    for _, linha in movimentacoes.iterrows():

        data = obter_campo(
            linha,
            ["Data", "data"],
        )

        detalhes = obter_campo(
            linha,
            ["Detalhes", "detalhes"],
        )

        lancamento = obter_campo(
            linha,
            ["Lançamento", "Lancamento", "lancamento"],
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

        registros.append({
            "Data": formatar_texto(data),
            "Detalhes": formatar_texto(detalhes),
            "Lançamento": formatar_texto(lancamento),
            "Valor": valor,
            "Tipo": formatar_texto(tipo),
            "Banco": formatar_texto(banco),
        })

    return pd.DataFrame(registros)


@st.dialog("Criar nova categoria")
def dialog_nova_categoria():

    with st.form("form_nova_categoria"):

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
            )

            if resultado == "invalida":
                st.warning("Informe um nome válido para a categoria.")

            elif resultado == "existente":
                st.warning("Essa categoria já está cadastrada.")

            else:
                limpar_cache_categorias()

                st.session_state["categoria_movimentacao_pendente"] = nome.strip()

                st.success("Categoria criada com sucesso!")

                st.rerun()



def render_painel_classificacao(linha, categorias):

    st.subheader("Classificar movimentação")

    with st.container(border=True):

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

        st.markdown(
            f"### {formatar_texto(detalhes)}"
        )

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

        categorias_validas = [
            categoria
            for categoria in categorias
        ]

        if st.button(
            "+ Nova categoria",
            key="nova_categoria_pendente",
        ):
            dialog_nova_categoria()

        opcoes_categorias = {
            categoria["categoria"]: categoria["id"]
            for categoria in categorias_validas
        }

        categoria_escolhida = st.selectbox(
            "Selecione uma categoria",
            options=list(opcoes_categorias.keys()),
            key="categoria_movimentacao_pendente",
        )

        categoria_id = opcoes_categorias[categoria_escolhida]

        cadastrar_palavra = st.checkbox(
            "Cadastrar palavra-chave para futuras movimentações",
            key="cadastrar_palavra_movimentacao",
        )

        palavra_chave = ""

        if cadastrar_palavra:

            palavra_chave = st.text_input(
                "Palavra-chave",
                placeholder="Ex.: MERCADO, UBER, FARMACIA...",
                key=f"palavra_chave_movimentacao_{obter_campo(linha, ['movimentacao_id', 'id'])}",
            )

        if st.button(
            "Salvar classificação",
            type="primary",
            width="stretch",
            key="salvar_classificacao_movimentacao",
        ):

            if cadastrar_palavra:

                resultado = verificar_regra_categorizacao(
                    palavra_chave,
                    categoria_id,
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

            movimentacao_id = obter_campo(
                linha,
                ["movimentacao_id", "id"],
            )

            sucesso = atualizar_categoria_manual(
                movimentacao_id,
                categoria_id,
            )

            if not sucesso:
                st.error("Não foi possível salvar a classificação.")
                return

            if cadastrar_palavra:

                cadastrar_regra_categorizacao(
                    palavra_chave,
                    categoria_id,
                )

            limpar_cache_categorias()

            st.success("Movimentação classificada com sucesso!")

            st.rerun()


@st.fragment
def _render_tabela_movimentacoes_pendentes(
    categorias,
    movimentacoes,
    df_movimentacoes,
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

    evento = st.dataframe(
        df_movimentacoes,
        hide_index=True,
        width="stretch",
        height=300,
        on_select="rerun",
        selection_mode="single-row",
        key="tabela_movimentacoes_pendentes",
    )

    linhas_selecionadas = evento.selection.rows

    if linhas_selecionadas:

        indice = linhas_selecionadas[0]

        if indice < len(movimentacoes):

            linha = movimentacoes.iloc[indice]

            render_painel_classificacao(
                linha,
                categorias,
            )

        else:

            st.info(
                "A lista de movimentações foi atualizada. "
                "Selecione novamente uma movimentação."
            )

    else:

        st.info("Selecione uma movimentação para classificar.")


def render_movimentacoes_pendentes():

    st.subheader("Movimentações pendentes")

    st.caption(
        "Classifique as movimentações que ainda não possuem "
        "uma categoria definida."
    )

    try:

        categorias = carregar_categorias()

        movimentacoes = carregar_movimentacoes_pendentes()

        indicadores = carregar_indicadores()

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

        if movimentacoes is None or movimentacoes.empty:

            st.success(
                "Todas as movimentações estão classificadas!"
            )
            return

        df_movimentacoes = preparar_tabela_movimentacoes(
            movimentacoes
        )

        _render_tabela_movimentacoes_pendentes(
            categorias,
            movimentacoes,
            df_movimentacoes,
        )

    except Exception as erro:

        st.error(
            f"Erro ao carregar movimentações pendentes: {erro}"
        )
