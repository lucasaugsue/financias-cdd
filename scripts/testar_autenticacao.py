
from getpass import getpass

from api.autenticacao import autenticar_usuario


email = input("E-mail: ").strip()
senha = getpass("Senha: ")

usuario = autenticar_usuario(email, senha)

if usuario:
    print("\nLogin realizado com sucesso!")
    print(f"Nome: {usuario['nome']}")
    print(f"ID: {usuario['id']}")
else:
    print("\nE-mail ou senha inválidos.")
