import streamlit as st

st.set_page_config(
    page_title="Financias CDD",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Financias CDD")
st.subheader("Seu ambiente de análise financeira")

st.write(
    "Bem-vindo ao seu painel de controle financeiro!"
)

st.info(
    "Em breve você poderá importar seus extratos bancários, "
    "acompanhar suas movimentações e visualizar análises financeiras."
)

st.divider()

col1, col2, col3 = st.columns(3)

col1.metric("Receitas", "R$ 0,00")
col2.metric("Despesas", "R$ 0,00")
col3.metric("Saldo", "R$ 0,00")

st.caption("Projeto pessoal de análise de dados financeiros.")