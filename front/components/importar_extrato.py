
import streamlit as st

from api.extratos import salvar_extrato

from services.arquivos import (
    ler_arquivo,
    calcular_hash_arquivo,
    limpar_extrato_banco_brasil,
)

from services.movimentacoes import padronizar_movimentacoes


@st.dialog("Importar novos extratos", width="large")
def dialog_importar_extrato():

    usuario_id = st.session_state["usuario"]["id"]

    bancos = [
        "Banco do Brasil",
        "Nubank",
        "Itaú",
        "Bradesco",
        "Caixa Econômica Federal",
        "Santander",
        "Inter",
        "Outro",
    ]

    st.write(
        "Selecione um ou mais arquivos para importar."
    )

    arquivos = st.file_uploader(
        "Selecione seus extratos",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key=f"modal_arquivos_{usuario_id}",
    )

    if not arquivos:
        return

    extratos_processados = []

    st.divider()

    st.subheader(
        f"Arquivos selecionados: {len(arquivos)}"
    )

    # Área com rolagem para os arquivos
    with st.container(height=550, border=True):

        for indice, arquivo in enumerate(arquivos):

            with st.expander(
                f"📄 {arquivo.name}",
                expanded=True,
            ):

                banco_origem = st.selectbox(
                    "Banco de origem",
                    bancos,
                    key=f"banco_{usuario_id}_{indice}_{arquivo.name}",
                )

                try:
                    # 1. Leitura original
                    df = ler_arquivo(arquivo)

                    quantidade_original = len(df)

                    # 2. Limpeza específica do Banco do Brasil
                    if (
                        banco_origem == "Banco do Brasil"
                        and arquivo.name.lower().endswith(".csv")
                    ):
                        df = limpar_extrato_banco_brasil(df)

                    quantidade_final = len(df)

                    registros_removidos = (
                        quantidade_original - quantidade_final
                    )

                    # 3. Cálculo do hash
                    hash_arquivo = calcular_hash_arquivo(
                        arquivo,
                        banco_origem,
                    )

                    # 4. Padronização
                    df = padronizar_movimentacoes(df)

                    # 5. Resumo
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
                            f"{registros_removidos} registro(s) "
                            "foram removidos pelas regras de limpeza."
                        )

                    st.caption(
                        f"Banco selecionado: {banco_origem}"
                    )

                    st.dataframe(
                        df,
                        width="stretch",
                        hide_index=True,
                    )

                    extratos_processados.append({
                        "arquivo": arquivo,
                        "banco_origem": banco_origem,
                        "hash_arquivo": hash_arquivo,
                        "df": df,
                    })

                except Exception as erro:
                    st.error(
                        f"Erro ao processar {arquivo.name}: {erro}"
                    )

    st.divider()

    # 6. Salvar todos os arquivos
    if st.button(
        "💾 Salvar todos os extratos",
        type="primary",
        width="stretch",
        key=f"salvar_todos_extratos_{usuario_id}",
    ):

        if not extratos_processados:
            st.warning(
                "Não existem arquivos válidos para importar."
            )
            return

        sucessos = 0
        falhas = 0

        with st.spinner("Salvando extratos..."):

            for extrato in extratos_processados:

                arquivo = extrato["arquivo"]
                df = extrato["df"]

                if df.empty:
                    st.warning(
                        f"{arquivo.name}: não possui movimentações válidas."
                    )
                    falhas += 1
                    continue

                try:
                    extrato_id = salvar_extrato(
                        arquivo.name,
                        extrato["banco_origem"],
                        extrato["hash_arquivo"],
                        df,
                        usuario_id,
                    )

                    st.success(
                        f"{arquivo.name}: salvo com sucesso! "
                        f"ID: {extrato_id}"
                    )

                    sucessos += 1

                except ValueError as erro:
                    st.warning(
                        f"{arquivo.name}: {erro}"
                    )
                    falhas += 1

                except Exception as erro:
                    st.error(
                        f"{arquivo.name}: erro ao salvar: {erro}"
                    )
                    falhas += 1

        st.divider()

        st.write(
            f"**Resultado:** {sucessos} arquivo(s) salvo(s) "
            f"e {falhas} arquivo(s) não importado(s)."
        )

        if sucessos > 0:
            st.rerun()
