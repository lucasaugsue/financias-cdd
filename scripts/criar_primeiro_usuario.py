
from getpass import getpass

from argon2 import PasswordHasher
from sqlalchemy import text

from api.connection import engine


def criar_primeiro_usuario():
    print("\n=== Criação do primeiro usuário ===\n")

    nome = input("Seu nome: ").strip()
    email = input("Seu e-mail: ").strip().lower()

    if not nome or not email:
        print("Nome e e-mail são obrigatórios.")
        return

    senha = getpass("Crie sua senha: ")
    confirmar_senha = getpass("Confirme sua senha: ")

    if not senha:
        print("A senha não pode ficar vazia.")
        return

    if senha != confirmar_senha:
        print("As senhas não coincidem.")
        return

    senha_hash = PasswordHasher().hash(senha)

    try:
        with engine.begin() as conn:

            quantidade_usuarios = conn.execute(
                text("SELECT COUNT(*) FROM usuarios")
            ).scalar_one()

            if quantidade_usuarios > 0:
                raise Exception(
                    "Já existe um usuário cadastrado. "
                    "A criação inicial foi cancelada."
                )

            registros_sem_usuario = conn.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM extratos
                         WHERE usuario_id IS NOT NULL)
                      + (SELECT COUNT(*) FROM categorias
                         WHERE usuario_id IS NOT NULL)
                      + (SELECT COUNT(*) FROM regras_categorizacao
                         WHERE usuario_id IS NOT NULL)
                """)
            ).scalar_one()

            if registros_sem_usuario > 0:
                raise Exception(
                    "Existem registros já associados a usuários. "
                    "Nenhuma alteração foi realizada."
                )

            usuario_id = conn.execute(
                text("""
                    INSERT INTO usuarios (nome, email, senha_hash)
                    VALUES (:nome, :email, :senha_hash)
                    RETURNING id
                """),
                {
                    "nome": nome,
                    "email": email,
                    "senha_hash": senha_hash,
                },
            ).scalar_one()

            conn.execute(
                text("""
                    UPDATE extratos
                    SET usuario_id = :usuario_id
                    WHERE usuario_id IS NULL
                """),
                {"usuario_id": usuario_id},
            )

            conn.execute(
                text("""
                    UPDATE categorias
                    SET usuario_id = :usuario_id
                    WHERE usuario_id IS NULL
                """),
                {"usuario_id": usuario_id},
            )

            conn.execute(
                text("""
                    UPDATE regras_categorizacao
                    SET usuario_id = :usuario_id
                    WHERE usuario_id IS NULL
                """),
                {"usuario_id": usuario_id},
            )

        print("\nUsuário criado com sucesso!")
        print(f"ID: {usuario_id}")
        print(f"E-mail: {email}")
        print("Dados existentes associados à sua conta.")

    except Exception as erro:
        print(f"\nErro: {erro}")
        print("Nenhuma alteração parcial foi mantida.")


if __name__ == "__main__":
    criar_primeiro_usuario()
