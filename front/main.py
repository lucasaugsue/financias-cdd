import streamlit as st

from api.extratos import criar_tabelas

from front.pages.movimentacoes import render_movimentacoes
from front.pages.extratos import render_extratos_salvos
from front.pages.graficos import render_graficos

from front.components.importar_extrato import (
    dialog_importar_extrato,
)


def render_app():

    st.set_page_config(
        page_title="Financias CDD",
        page_icon="💰",
        layout="wide",
    )

    # Criar tabelas caso ainda não existam
    try:
        criar_tabelas()

    except Exception as erro:
        st.error(
            f"Erro ao conectar com o banco: {erro}"
        )
        return

    # Cabeçalho
    col1, col2 = st.columns([5, 1])

    with col1:
        st.title("💰 Financias CDD")
        st.caption(
            "Seu gerenciador financeiro pessoal"
        )

    with col2:
        st.write("")
        st.write("")

        if st.button(
            "📥 Importar extrato",
            type="primary",
            use_container_width=True,
        ):
            dialog_importar_extrato()

    # Navegação principal
    aba_movimentacoes, aba_graficos, aba_extratos = st.tabs([
        "📊 Todas as movimentações",
        "📈 Gráficos",
        "📂 Extratos salvos",
    ])

    with aba_movimentacoes:
        render_movimentacoes()

    with aba_graficos:
        render_graficos()

    with aba_extratos:
        render_extratos_salvos()
