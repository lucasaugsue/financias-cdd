
import streamlit as st

from api.autenticacao import (
    autenticar_usuario,
    cadastrar_usuario,
)


def render_login():

    st.title("💰 Financias CDD")
    st.caption("Seu gerenciador financeiro pessoal")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    # LOGIN
    with aba_login:

        st.subheader("Acessar sua conta")

        with st.form("form_login"):

            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")

            enviar = st.form_submit_button(
                "Entrar",
                use_container_width=True,
            )

            if enviar:

                usuario = autenticar_usuario(email, senha)

                if usuario:
                    st.session_state["usuario"] = usuario
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

    # CADASTRO
    with aba_cadastro:

        st.subheader("Criar uma conta")

        with st.form("form_cadastro"):

            nome = st.text_input("Nome")
            email = st.text_input("E-mail", key="cadastro_email")
            senha = st.text_input(
                "Senha",
                type="password",
                key="cadastro_senha",
            )
            confirmar_senha = st.text_input(
                "Confirmar senha",
                type="password",
            )

            enviar = st.form_submit_button(
                "Criar conta",
                use_container_width=True,
            )

            if enviar:

                if senha != confirmar_senha:
                    st.error("As senhas não coincidem.")

                else:
                    sucesso, resultado = cadastrar_usuario(
                        nome,
                        email,
                        senha,
                    )

                    if sucesso:
                        st.success("Conta criada com sucesso!")

                        st.session_state["usuario"] = {
                            "id": resultado,
                            "nome": nome.strip(),
                            "email": email.strip().lower(),
                        }

                        st.rerun()

                    else:
                        st.error(resultado)
