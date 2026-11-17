
import json

import pandas as pd
from sqlalchemy import text

from api.connection import engine


def criar_tabelas():
    """Cria as tabelas necessárias caso ainda não existam."""

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS extratos (
                id SERIAL PRIMARY KEY,
                nome_arquivo TEXT NOT NULL,
                banco_origem TEXT NOT NULL,
                hash_arquivo VARCHAR(64) UNIQUE NOT NULL,
                quantidade_registros INTEGER NOT NULL DEFAULT 0,
                criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id SERIAL PRIMARY KEY,
                extrato_id INTEGER NOT NULL
                    REFERENCES extratos(id) ON DELETE CASCADE,
                dados JSONB NOT NULL
            );
        """))

        connection.execute(text("""
            ALTER TABLE extratos
            ADD COLUMN IF NOT EXISTS banco_origem TEXT;
        """))

        connection.execute(text("""
            UPDATE extratos
            SET banco_origem = 'Banco do Brasil'
            WHERE banco_origem IS NULL;
        """))

        connection.execute(text("""
            ALTER TABLE extratos
            ALTER COLUMN banco_origem SET NOT NULL;
        """))


def listar_extratos():
    """Retorna os extratos salvos."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT
                id,
                nome_arquivo,
                banco_origem,
                quantidade_registros,
                criado_em
            FROM extratos
            ORDER BY criado_em DESC;
        """))

        return [dict(linha) for linha in resultado.mappings().all()]


def buscar_movimentacoes(extrato_id):
    """Busca as movimentações de um extrato."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT dados
                FROM movimentacoes
                WHERE extrato_id = :extrato_id
                ORDER BY id;
            """),
            {"extrato_id": extrato_id}
        )

        registros = [linha[0] for linha in resultado.fetchall()]

    return pd.DataFrame(registros)


def salvar_extrato(nome_arquivo, banco_origem, hash_arquivo, df):
    """Salva um novo extrato e suas movimentações."""

    registros = json.loads(
        df.to_json(
            orient="records",
            date_format="iso",
            force_ascii=False
        )
    )

    with engine.begin() as connection:

        duplicado = connection.execute(
            text("""
                SELECT id
                FROM extratos
                WHERE hash_arquivo = :hash_arquivo;
            """),
            {"hash_arquivo": hash_arquivo}
        ).first()

        if duplicado:
            raise ValueError("Este arquivo já foi importado.")

        resultado = connection.execute(
            text("""
                INSERT INTO extratos (
                    nome_arquivo,
                    banco_origem,
                    hash_arquivo,
                    quantidade_registros
                )
                VALUES (
                    :nome,
                    :banco,
                    :hash,
                    :quantidade
                )
                RETURNING id;
            """),
            {
                "nome": nome_arquivo, 
                "banco": banco_origem,
                "hash": hash_arquivo,
                "quantidade": len(registros)
            }
        )

        extrato_id = resultado.scalar_one()

        if registros:
            connection.execute(
                text("""
                    INSERT INTO movimentacoes (extrato_id, dados)
                    VALUES (
                        :extrato_id,
                        CAST(:dados AS JSONB)
                    );
                """),
                [
                    {
                        "extrato_id": extrato_id,
                        "dados": json.dumps(
                            registro,
                            ensure_ascii=False
                        )
                    }
                    for registro in registros
                ]
            )

    return extrato_id


def atualizar_extrato(extrato_id, df):
    """Substitui as movimentações pelas versões editadas."""

    registros = json.loads(
        df.to_json(
            orient="records",
            date_format="iso",
            force_ascii=False
        )
    )

    with engine.begin() as connection:

        existe = connection.execute(
            text("SELECT id FROM extratos WHERE id = :id"),
            {"id": extrato_id}
        ).first()

        if not existe:
            raise ValueError("Extrato não encontrado.")

        connection.execute(
            text("""
                DELETE FROM movimentacoes
                WHERE extrato_id = :extrato_id;
            """),
            {"extrato_id": extrato_id}
        )

        if registros:
            connection.execute(
                text("""
                    INSERT INTO movimentacoes (extrato_id, dados)
                    VALUES (
                        :extrato_id,
                        CAST(:dados AS JSONB)
                    );
                """),
                [
                    {
                        "extrato_id": extrato_id,
                        "dados": json.dumps(
                            registro,
                            ensure_ascii=False
                        )
                    }
                    for registro in registros
                ]
            )

        connection.execute(
            text("""
                UPDATE extratos
                SET quantidade_registros = :quantidade
                WHERE id = :extrato_id;
            """),
            {
                "quantidade": len(registros),
                "extrato_id": extrato_id
            }
        )


def excluir_extrato(extrato_id):
    """Exclui um extrato e suas movimentações."""

    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM extratos WHERE id = :id"),
            {"id": extrato_id}
        )


def listar_movimentacoes_consolidadas():
    """Retorna movimentações de todos os extratos com o banco de origem."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT
                m.id AS movimentacao_id,
                m.extrato_id,
                e.banco_origem,
                e.nome_arquivo,
                m.dados
            FROM movimentacoes m
            INNER JOIN extratos e
                ON e.id = m.extrato_id
            ORDER BY e.banco_origem, m.id;
        """))

        linhas = resultado.mappings().all()

    registros = []

    for linha in linhas:
        registro = dict(linha["dados"])

        registro["movimentacao_id"] = linha["movimentacao_id"]
        registro["extrato_id"] = linha["extrato_id"]
        registro["banco_origem"] = linha["banco_origem"]
        registro["arquivo_origem"] = linha["nome_arquivo"]

        registros.append(registro)

    return pd.DataFrame(registros)

