
import os

from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy import text

from api.connection import engine


load_dotenv()

password_hasher = PasswordHasher()

TEMPO_SESSAO = 60 * 60 * 24  # 24 horas


def criar_serializer():
    chave_secreta = os.getenv("SECRET_KEY")

    if not chave_secreta:
        raise ValueError("SECRET_KEY não configurada no arquivo .env.")

    return URLSafeTimedSerializer(
        chave_secreta,
        salt="financias-cdd-auth",
    )


def gerar_token_sessao(usuario_id):
    serializer = criar_serializer()

    return serializer.dumps({
        "usuario_id": int(usuario_id),
    })


def validar_token_sessao(token):
    if not token:
        return None

    try:
        serializer = criar_serializer()

        dados = serializer.loads(
            token,
            max_age=TEMPO_SESSAO,
        )

        usuario_id = dados.get("usuario_id")

        with engine.connect() as conn:
            usuario = conn.execute(
                text("""
                    SELECT id, nome, email
                    FROM usuarios
                    WHERE id = :usuario_id
                    AND ativo = TRUE
                """),
                {"usuario_id": usuario_id},
            ).mappings().first()

        if not usuario:
            return None

        return {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
        }

    except (BadSignature, TypeError, ValueError):
        return None


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
