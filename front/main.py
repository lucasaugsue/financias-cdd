
import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

from api.extratos import (
    criar_tabelas,
    listar_extratos,
    buscar_movimentacoes,
    salvar_extrato,
    atualizar_extrato,
    excluir_extrato,
    listar_movimentacoes_consolidadas
)


def ler_arquivo(arquivo):
    nome = arquivo.name.lower()
    conteudo = arquivo.getvalue()

    if nome.endswith(".csv"):
        try:
            return pd.read_csv(
                BytesIO(conteudo),
                sep=None,
                engine="python",
                encoding="utf-8-sig"
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                BytesIO(conteudo),
                sep=None,
                engine="python",
                encoding="latin1"
            )

    if nome.endswith(".xlsx"):
        return pd.read_excel(
            BytesIO(conteudo),
            engine="openpyxl"
        )

    raise ValueError("Formato de arquivo não suportado.")


def render_app():

    st.set_page_config(
        page_title="Financias CDD",
        page_icon="💰",
        layout="wide"
    )

    st.title("💰 Financias CDD")
    st.write("Gerenciador de extratos bancários")

    # Cria as tabelas caso ainda não existam
    try:
        criar_tabelas()
    except Exception as erro:
        st.error(f"Erro ao conectar com o banco: {erro}")
        return

    aba_importar, aba_extratos, aba_consolidado = st.tabs([
        "📥 Importar extrato",
        "📂 Extratos salvos",
        "📊 Movimentações consolidadas"
    ])

    # -----------------------------------------
    # ABA 1 - IMPORTAÇÃO
    # -----------------------------------------

    with aba_importar:

        st.subheader("Importar novo extrato")

        banco_origem = st.selectbox(
            "Selecione o banco de origem",
            [
                "Banco do Brasil",
                "Nubank",
                "Itaú",
                "Bradesco",
                "Caixa Econômica Federal",
                "Santander",
                "Inter",
                "Outro"
            ]
        )

        arquivo = st.file_uploader(
            "Selecione seu extrato",
            type=["csv", "xlsx"],
            accept_multiple_files=False
        )

        if arquivo is not None:

            try:
                df = ler_arquivo(arquivo)

                conteudo = arquivo.getvalue()
                hash_arquivo = hashlib.sha256(
                    banco_origem.encode("utf-8") + b":" + conteudo
                ).hexdigest()

                st.success(
                    f"Arquivo carregado: {arquivo.name}"
                )

                col1, col2 = st.columns(2)

                col1.metric(
                    "Quantidade de registros",
                    len(df)
                )

                col2.metric(
                    "Quantidade de colunas",
                    len(df.columns)
                )

                st.subheader("Prévia das movimentações")

                st.dataframe(
                    df,
                    width="stretch",
                    hide_index=True
                )

                if st.button(
                    "💾 Salvar extrato no banco",
                    type="primary"
                ):

                    try:
                        extrato_id = salvar_extrato(
                            arquivo.name,
                            banco_origem,
                            hash_arquivo,
                            df
                        )

                        st.success(
                            f"Extrato salvo com sucesso! ID: {extrato_id}"
                        )

                    except ValueError as erro:
                        st.warning(str(erro))

                    except Exception as erro:
                        st.error(
                            f"Erro ao salvar extrato: {erro}"
                        )

            except Exception as erro:
                st.error(
                    f"Não foi possível ler o arquivo: {erro}"
                )

    # -----------------------------------------
    # ABA 2 - EXTRATOS SALVOS
    # -----------------------------------------

    with aba_extratos:

        st.subheader("Meus extratos")

        try:
            extratos = listar_extratos()

            if not extratos:
                st.info(
                    "Você ainda não possui extratos salvos."
                )

            else:

                st.metric(
                    "Total de extratos",
                    len(extratos)
                )

                df_extratos = pd.DataFrame(extratos)

                st.dataframe(
                    df_extratos,
                    width="stretch",
                    hide_index=True
                )

                st.divider()

                st.subheader("Consultar e editar extrato")

                opcoes = {
                    f"{item['nome_arquivo']} (ID: {item['id']})":
                    item["id"]
                    for item in extratos
                }

                selecionado = st.selectbox(
                    "Selecione um extrato",
                    options=list(opcoes.keys())
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
                    key=f"editor_{extrato_id}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "💾 Salvar alterações",
                        type="primary"
                    ):
                        try:
                            atualizar_extrato(
                                extrato_id,
                                df_editado
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
                        "Confirmo que desejo excluir este extrato"
                    )

                    if st.button(
                        "🗑️ Excluir extrato",
                        disabled=not confirmar
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

    # -----------------------------------------
    # ABA 3 - MOVIMENTAÇÕES CONSOLIDADAS
    # -----------------------------------------

    with aba_consolidado:

        st.subheader("Todas as movimentações")

        try:
            df_consolidado = listar_movimentacoes_consolidadas()

            if df_consolidado.empty:
                st.info("Ainda não existem movimentações cadastradas.")

            else:

                # Identificar coluna de data
                coluna_data = next(
                    (
                        coluna for coluna in df_consolidado.columns
                        if coluna.lower() in ["data", "date"]
                    ),
                    None
                )

                if coluna_data:
                    df_consolidado[coluna_data] = pd.to_datetime(
                        df_consolidado[coluna_data],
                        errors="coerce"
                    ).dt.date

                # Identificar coluna de tipo de lançamento
                coluna_tipo = next(
                    (
                        coluna for coluna in df_consolidado.columns
                        if coluna.lower() in [
                            "tipo_lancamento",
                            "tipo de lançamento",
                            "tipo de lancamento",
                            "tipo"
                        ]
                    ),
                    None
                )

                # ---------------------------------
                # FILTROS
                # ---------------------------------

                st.markdown("### Filtros")

                col1, col2, col3, col4 = st.columns(4)

                # Filtro de banco
                with col1:
                    bancos = ["Todos"] + sorted(
                        df_consolidado["banco_origem"]
                        .dropna()
                        .unique()
                        .tolist()
                    )

                    banco_filtro = st.selectbox(
                        "Banco",
                        bancos
                    )

                # Filtro de período
                with col2:
                    if coluna_data and df_consolidado[coluna_data].notna().any():

                        data_minima = df_consolidado[coluna_data].min()
                        data_maxima = df_consolidado[coluna_data].max()

                        periodo = st.date_input(
                            "Período",
                            value=(data_minima, data_maxima),
                            min_value=data_minima,
                            max_value=data_maxima,
                            format="DD/MM/YYYY"
                        )

                    else:
                        periodo = ()

                        st.caption(
                            "Não foi encontrada uma coluna de data."
                        )

                # Filtro de tipo de lançamento
                with col3:
                    if coluna_tipo:
                        tipos = ["Todos"] + sorted(
                            df_consolidado[coluna_tipo]
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        tipo_filtro = st.selectbox(
                            "Tipo de lançamento",
                            tipos
                        )

                    else:
                        tipo_filtro = "Todos"

                        st.caption(
                            "Coluna de tipo não encontrada."
                        )

                # Filtro de arquivo de origem
                with col4:
                    arquivos = ["Todos"] + sorted(
                        df_consolidado["arquivo_origem"]
                        .dropna()
                        .unique()
                        .tolist()
                    )

                    arquivo_filtro = st.selectbox(
                        "Arquivo de origem",
                        arquivos
                    )

                # ---------------------------------
                # APLICAR FILTROS
                # ---------------------------------

                df_filtrado = df_consolidado.copy()

                if banco_filtro != "Todos":
                    df_filtrado = df_filtrado[
                        df_filtrado["banco_origem"] == banco_filtro
                    ]

                if (
                    coluna_data
                    and isinstance(periodo, (tuple, list))
                    and len(periodo) == 2
                ):
                    data_inicio, data_final = periodo

                    df_filtrado = df_filtrado[
                        df_filtrado[coluna_data].between(
                            data_inicio,
                            data_final
                        )
                    ]

                if coluna_tipo and tipo_filtro != "Todos":
                    df_filtrado = df_filtrado[
                        df_filtrado[coluna_tipo].astype(str) == tipo_filtro
                    ]

                if arquivo_filtro != "Todos":
                    df_filtrado = df_filtrado[
                        df_filtrado["arquivo_origem"] == arquivo_filtro
                    ]

                # ---------------------------------
                # RESULTADOS
                # ---------------------------------

                st.divider()

                col1, col2 = st.columns(2)

                col1.metric(
                    "Total de movimentações",
                    len(df_filtrado)
                )

                col2.metric(
                    "Bancos identificados",
                    df_filtrado["banco_origem"].nunique()
                )

                st.dataframe(
                    df_filtrado,
                    width="stretch",
                    hide_index=True
                )

        except Exception as erro:
            st.error(
                f"Erro ao consultar movimentações: {erro}"
            )
