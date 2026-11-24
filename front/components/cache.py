
import streamlit as st

from api.categorias import (
    listar_categorias,
    listar_regras_categorizacao,
)

from api.extratos import (
    listar_movimentacoes_pendentes,
    contar_movimentacoes_categorizadas,
)


@st.cache_data(ttl=60)
def carregar_categorias(usuario_id):
    return listar_categorias(usuario_id)


@st.cache_data(ttl=60)
def carregar_regras(usuario_id):
    return listar_regras_categorizacao(usuario_id)


@st.cache_data(ttl=60)
def carregar_movimentacoes_pendentes(usuario_id):
    return listar_movimentacoes_pendentes(usuario_id)


@st.cache_data(ttl=60)
def carregar_indicadores(usuario_id):
    return contar_movimentacoes_categorizadas(usuario_id)


def limpar_cache_categorias():

    carregar_categorias.clear()
    carregar_regras.clear()
    carregar_movimentacoes_pendentes.clear()
    carregar_indicadores.clear()
