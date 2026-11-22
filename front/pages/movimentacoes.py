import streamlit as st

from front.components.filtros import render_filtros
from front.components.indicadores import render_indicadores

from api.extratos import (
    listar_movimentacoes_consolidadas,
    atualizar_categorias_movimentacoes,
    editar_categoria_movimentacao,
)

from api.categorias import listar_categorias

from services.movimentacoes import (
    preparar_movimentacoes,
    converter_valor_monetario,
    categorizar_movimentacoes,
)


@st.dialog("Detalhes da movimentação", dismissible=False)
def dialog_movimentacao(linha):

    categorias = listar_categorias()

    movimentacao_id = int(linha["movimentacao_id"])

    st.subheader(
        linha.get("Lançamento", "Movimentação")
    )

    valor = converter_valor_monetario(
        linha.get("Valor", 0)
    )

    st.metric(
        "Valor",
        f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    st.divider()

    st.write("**Data:**", linha.get("Data", "Não informada"))
    st.write("**Banco:**", linha.get("banco_origem", "Não informado"))
    st.write("**Descrição:**", linha.get("Detalhes", "Não informado"))

    st.divider()

    st.subheader("Editar categoria")

    nomes_categorias = {
        categoria["id"]: categoria["categoria"]
        for categoria in categorias
    }

    categoria_atual = linha.get("categoria_id")

    opcoes = [None] + list(nomes_categorias.keys())

    indice_atual = (
        opcoes.index(int(categoria_atual))
        if categoria_atual is not None
        else 0
    )

    nova_categoria = st.selectbox(
        "Selecione a categoria",
        options=opcoes,
        index=indice_atual,
        format_func=lambda categoria_id: (
            "Sem categoria"
            if categoria_id is None
            else nomes_categorias[categoria_id]
        ),
        key=f"editar_categoria_{movimentacao_id}",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Fechar", use_container_width=True):
            st.rerun()

    with col2:
        if st.button(
            "Salvar alteração",
            type="primary",
            use_container_width=True,
        ):

            sucesso = editar_categoria_movimentacao(
                movimentacao_id,
                nova_categoria,
            )

            if sucesso:
                st.session_state["limpar_selecao_movimentacoes"] = True
                st.success("Categoria atualizada com sucesso!")
                st.rerun()

            else:
                st.error("Não foi possível atualizar a categoria.")


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
            "categoria_id",
            "palavra_chave_identificada",
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
        
        # Inicializa o controle da tabela
        if "versao_tabela_movimentacoes" not in st.session_state:
            st.session_state["versao_tabela_movimentacoes"] = 0

        if "assinatura_filtros_movimentacoes" not in st.session_state:
            st.session_state["assinatura_filtros_movimentacoes"] = None

        # Identifica alterações nos filtros
        assinatura_filtros = (
            tuple(st.session_state.get("filtro_periodos", [])),
            st.session_state.get("filtro_banco", "Todos"),
            st.session_state.get("filtro_tipo", "Todos"),
            st.session_state.get("filtro_categoria", "Todos"),
        )

        if (
            st.session_state["assinatura_filtros_movimentacoes"] is not None
            and st.session_state["assinatura_filtros_movimentacoes"] != assinatura_filtros
        ):
            st.session_state["versao_tabela_movimentacoes"] += 1

        st.session_state["assinatura_filtros_movimentacoes"] = assinatura_filtros

        # Tabela de movimentações
        chave_tabela = (
            f"tabela_todas_movimentacoes_"
            f"{st.session_state['versao_tabela_movimentacoes']}"
        )

        evento_tabela = st.dataframe(
            df_visualizacao,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=chave_tabela,
        )

        # Verifica se alguma movimentação foi selecionada
        linhas_selecionadas = evento_tabela.selection.rows

        if linhas_selecionadas:

            indice = linhas_selecionadas[0]

            if indice < len(df_filtrado):

                linha_selecionada = df_filtrado.iloc[indice]

                st.session_state["versao_tabela_movimentacoes"] += 1

                dialog_movimentacao(linha_selecionada)



    except Exception as erro:
        st.error(
            f"Erro ao consultar movimentações: {erro}"
        )
