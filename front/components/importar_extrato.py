
import streamlit as st

from api.extratos import salvar_extrato
from services.arquivos import ler_arquivo, calcular_hash_arquivo


@st.dialog("Importar novo extrato", width="large")
def dialog_importar_extrato():

    st.write(
        "Selecione o banco e o arquivo que deseja importar."
    )

    banco_origem = st.selectbox(
        "Banco de origem",
        [
            "Banco do Brasil",
            "Nubank",
            "Itaú",
            "Bradesco",
            "Caixa Econômica Federal",
            "Santander",
            "Inter",
            "Outro",
        ],
        key="modal_banco_origem",
    )

    arquivo = st.file_uploader(
        "Selecione seu extrato",
        type=["csv", "xlsx"],
        accept_multiple_files=False,
        key="modal_arquivo",
    )

    if arquivo is None:
        return

    try:
        df = ler_arquivo(arquivo)

        hash_arquivo = calcular_hash_arquivo(
            arquivo,
            banco_origem,
        )

        st.success(
            f"Arquivo carregado: {arquivo.name}"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Quantidade de registros",
            len(df),
        )

        col2.metric(
            "Quantidade de colunas",
            len(df.columns),
        )

        st.subheader("Prévia das movimentações")

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
        )

        if st.button(
            "💾 Salvar extrato no banco",
            type="primary",
            use_container_width=True,
        ):

            try:
                with st.spinner("Salvando extrato..."):

                    extrato_id = salvar_extrato(
                        arquivo.name,
                        banco_origem,
                        hash_arquivo,
                        df,
                    )

                st.success(
                    f"Extrato salvo com sucesso! ID: {extrato_id}"
                )

                st.rerun()

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
