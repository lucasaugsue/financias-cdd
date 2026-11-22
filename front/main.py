
import streamlit as st

from api.extratos import criar_tabelas
from api.categorias import criar_categorias_padrao

from front.pages.movimentacoes import render_movimentacoes
from front.pages.extratos import render_extratos_salvos
from front.pages.graficos import render_graficos
from front.pages.movimentacoes_pendentes import render_movimentacoes_pendentes
from front.pages.categorias import render_categorias


def render_app():

    st.set_page_config(
        page_title="Financias CDD",
        page_icon="💰",
        layout="wide",
    )

    try:
        criar_tabelas()
        criar_categorias_padrao()

    except Exception as erro:
        st.error(
            f"Erro ao conectar com o banco: {erro}"
        )
        return

    # Cabeçalho
    st.title("💰 Financias CDD")
    st.caption("Seu gerenciador financeiro pessoal")

    # Navegação principal
    (
        aba_movimentacoes,
        aba_graficos,
        aba_pendentes,
        aba_categorias,
        aba_extratos,
    ) = st.tabs([
        "📊 Todas as movimentações",
        "📈 Gráficos",
        "📋 Movimentações pendentes",
        "🏷️ Gerenciar categorias",
        "📂 Extratos salvos",
    ])

    with aba_movimentacoes:
        render_movimentacoes()

    with aba_graficos:
        render_graficos()

    with aba_pendentes:
        render_movimentacoes_pendentes()

    with aba_categorias:
        render_categorias()

    with aba_extratos:
        render_extratos_salvos()
