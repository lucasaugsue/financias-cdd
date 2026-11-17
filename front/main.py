
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
    excluir_extrato
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

    aba_importar, aba_extratos = st.tabs([
        "📥 Importar extrato",
        "📂 Extratos salvos"
    ])

    # -----------------------------------------
    # ABA 1 - IMPORTAÇÃO
    # -----------------------------------------

    with aba_importar:

        st.subheader("Importar novo extrato")

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
                    conteudo
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
