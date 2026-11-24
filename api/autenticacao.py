
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy import text

from api.connection import engine


password_hasher = PasswordHasher()


def cadastrar_usuario(nome, email, senha):
    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not email or not senha:
        return False, "Preencha todos os campos."

    senha_hash = password_hasher.hash(senha)

    try:
        with engine.begin() as conn:
            usuario = conn.execute(
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

        return True, usuario

    except Exception as erro:
        if "idx_usuarios_email" in str(erro) or "unique" in str(erro).lower():
            return False, "Este e-mail já está cadastrado."

        return False, "Não foi possível cadastrar o usuário."


def autenticar_usuario(email, senha):
    email = email.strip().lower()

    if not email or not senha:
        return None

    with engine.connect() as conn:
        usuario = conn.execute(
            text("""
                SELECT id, nome, email, senha_hash, ativo
                FROM usuarios
                WHERE LOWER(TRIM(email)) = :email
            """),
            {"email": email},
        ).mappings().first()

    if not usuario or not usuario["ativo"]:
        return None

    try:
        senha_valida = password_hasher.verify(
            usuario["senha_hash"],
            senha,
        )

        if not senha_valida:
            return None

        return {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
        }

    except (VerifyMismatchError, VerificationError):
        return None
