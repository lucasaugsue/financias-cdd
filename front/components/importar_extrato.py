
import streamlit as st

from api.extratos import salvar_extrato

from services.arquivos import (
    ler_arquivo,
    calcular_hash_arquivo,
    limpar_extrato_banco_brasil,
)

from services.movimentacoes import padronizar_movimentacoes


@st.dialog("Importar novo extrato", width="large")
def dialog_importar_extrato():

    usuario_id = st.session_state["usuario"]["id"]

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
        key=f"modal_banco_origem_{usuario_id}",
    )

    arquivo = st.file_uploader(
        "Selecione seu extrato",
        type=["csv", "xlsx"],
        accept_multiple_files=False,
        key=f"modal_arquivo_{usuario_id}",
    )

    if arquivo is None:
        return

    try:
        # 1. Leitura original do arquivo
        df = ler_arquivo(arquivo)

        quantidade_original = len(df)

        # 2. Aplicação das regras específicas do Banco do Brasil
        if (
            banco_origem == "Banco do Brasil"
            and arquivo.name.lower().endswith(".csv")
        ):
            df = limpar_extrato_banco_brasil(df)

        quantidade_final = len(df)
        registros_removidos = quantidade_original - quantidade_final

        # 3. Cálculo do hash do arquivo original
        hash_arquivo = calcular_hash_arquivo(
            arquivo,
            banco_origem,
        )

        # 4. Padronização das movimentações
        df = padronizar_movimentacoes(df)

        st.success(
            f"Arquivo carregado: {arquivo.name}"
        )

        # 5. Resumo da importação
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Registros originais",
            quantidade_original,
        )

        col2.metric(
            "Registros removidos",
            registros_removidos,
        )

        col3.metric(
            "Registros para importar",
            quantidade_final,
        )

        if registros_removidos > 0:
            st.info(
                f"{registros_removidos} registro(s) foram removidos "
                "pelas regras de limpeza do Banco do Brasil."
            )

        # 6. Prévia dos dados padronizados
        st.subheader("Prévia das movimentações")

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
        )

        # 7. Salvamento no banco
        if st.button(
            "💾 Salvar extrato no banco",
            type="primary",
            width="stretch",
            key=f"salvar_extrato_{usuario_id}",
        ):

            if df.empty:
                st.warning(
                    "Não existem movimentações válidas para importar."
                )
                return

            try:
                with st.spinner("Salvando extrato..."):

                    extrato_id = salvar_extrato(
                        arquivo.name,
                        banco_origem,
                        hash_arquivo,
                        df,
                        usuario_id,
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
