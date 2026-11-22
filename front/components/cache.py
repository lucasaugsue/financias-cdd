
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
def carregar_categorias():
    return listar_categorias()


@st.cache_data(ttl=60)
def carregar_regras():
    return listar_regras_categorizacao()


@st.cache_data(ttl=60)
def carregar_movimentacoes_pendentes():
    return listar_movimentacoes_pendentes()


@st.cache_data(ttl=60)
def carregar_indicadores():
    return contar_movimentacoes_categorizadas()


def limpar_cache_categorias():

    carregar_categorias.clear()
    carregar_regras.clear()
    carregar_movimentacoes_pendentes.clear()
    carregar_indicadores.clear()
