
import streamlit as st
import extra_streamlit_components as stx

from api.extratos import criar_tabelas
from api.categorias import criar_categorias_padrao
from api.autenticacao import validar_token_sessao

from front.pages.login import render_login

from front.pages.movimentacoes import render_movimentacoes
from front.pages.extratos import render_extratos_salvos
from front.pages.graficos import render_graficos
from front.pages.movimentacoes_pendentes import render_movimentacoes_pendentes
from front.pages.categorias import render_categorias

from front.components.cache import limpar_cache_categorias


def render_app():

    st.set_page_config(
        page_title="Financias CDD",
        page_icon="💰",
        layout="wide",
    )

    # Inicialização do banco
    try:
        criar_tabelas()

    except Exception as erro:
        st.error(f"Erro ao conectar com o banco: {erro}")
        return

    # Gerenciador de cookies
    cookie_manager = stx.CookieManager(key="financias_cookie_manager")
    cookies = cookie_manager.get_all() or {}

    # Recupera o usuário pela sessão salva no navegador
    usuario = st.session_state.get("usuario")

    if not usuario:
        token = cookies.get("financias_sessao")

        if token:
            usuario = validar_token_sessao(token)

            if usuario:
                st.session_state["usuario"] = usuario

    # Se não houver sessão válida, mostra o login
    if not usuario:
        render_login(cookie_manager)
        return

    usuario_id = usuario["id"]

    # Cria as categorias padrão do usuário, caso ainda não existam
    try:
        criar_categorias_padrao(usuario_id)

    except Exception as erro:
        st.error(f"Erro ao carregar as categorias: {erro}")
        return

    # Estilização do cabeçalho
    st.markdown(
        """
        <style>
        .st-key-cabecalho {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: var(--background-color);
            padding: 0.8rem 0;
            border-bottom: 1px solid var(--secondary-background-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Cabeçalho superior
    with st.container(key="cabecalho"):

        coluna_titulo, coluna_usuario, coluna_sair = st.columns(
            [5, 2, 1],
            vertical_alignment="center",
        )

        with coluna_titulo:
            st.markdown("### 💰 Financias CDD")

        with coluna_usuario:
            st.markdown(f"Olá, **{usuario['nome']}**!")

        with coluna_sair:
            if st.button("Sair", use_container_width=True):
                limpar_cache_categorias()

                st.session_state.pop("usuario", None)
                st.session_state.pop("token_sessao", None)

                cookie_manager.delete("financias_sessao")

                st.rerun()

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
