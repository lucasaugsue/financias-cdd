import json

import pandas as pd
from sqlalchemy import text

from api.connection import engine


def criar_tabelas():
    """Cria e atualiza a estrutura das tabelas do banco."""

    with engine.begin() as connection:

        # Tabela de extratos
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

        # Tabela de categorias
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                categoria TEXT UNIQUE NOT NULL,
                finalidade TEXT NOT NULL
                    CHECK (finalidade IN ('Receita', 'Despesa', 'Ambas'))
            );
        """))

        # Tabela de movimentações
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id SERIAL PRIMARY KEY,
                extrato_id INTEGER NOT NULL
                    REFERENCES extratos(id) ON DELETE CASCADE,
                categoria_id INTEGER
                    REFERENCES categorias(id) ON DELETE SET NULL,
                dados JSONB NOT NULL
            );
        """))

        # Tabela de regras de categorização
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS regras_categorizacao (
                id SERIAL PRIMARY KEY,
                palavra_chave TEXT NOT NULL,
                categoria_id INTEGER NOT NULL
                    REFERENCES categorias(id) ON DELETE CASCADE,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (TRIM(palavra_chave) <> '')
            );
        """))

        # Impedir palavras duplicadas na mesma categoria
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_regra_palavra_categoria
            ON regras_categorizacao (
                LOWER(TRIM(palavra_chave)),
                categoria_id
            );
        """))

        # Migração para bancos que já possuem a tabela movimentacoes
        connection.execute(text("""
            ALTER TABLE movimentacoes
            ADD COLUMN IF NOT EXISTS categoria_id INTEGER;
        """))

        # Garante a chave estrangeira mesmo em bancos já existentes
        connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'fk_movimentacoes_categoria'
                ) THEN
                    ALTER TABLE movimentacoes
                    ADD CONSTRAINT fk_movimentacoes_categoria
                    FOREIGN KEY (categoria_id)
                    REFERENCES categorias(id)
                    ON DELETE SET NULL;
                END IF;
            END $$;
        """))

        # Mantém a compatibilidade com extratos antigos
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
                SELECT id, extrato_id, dados
                FROM movimentacoes
                WHERE extrato_id = :extrato_id
                ORDER BY id;
            """),
            {"extrato_id": extrato_id}
        )

        registros = resultado.fetchall()

    df = pd.DataFrame([registro.dados for registro in registros])

    return df


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
                m.categoria_id,
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
        registro["categoria_id"] = linha["categoria_id"]
        registro["extrato_id"] = linha["extrato_id"]
        registro["banco_origem"] = linha["banco_origem"]
        registro["arquivo_origem"] = linha["nome_arquivo"]

        registros.append(registro)

    return pd.DataFrame(registros)


def listar_movimentacoes_pendentes():
    """Retorna movimentações que ainda não possuem categoria."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT
                m.id AS movimentacao_id,
                m.extrato_id,
                e.banco_origem,
                m.dados
            FROM movimentacoes m
            INNER JOIN extratos e
                ON e.id = m.extrato_id
            WHERE m.categoria_id IS NULL
            ORDER BY m.id;
        """))

        linhas = resultado.mappings().all()

    registros = []

    for linha in linhas:
        registro = dict(linha["dados"])

        registro["movimentacao_id"] = linha["movimentacao_id"]
        registro["extrato_id"] = linha["extrato_id"]
        registro["banco_origem"] = linha["banco_origem"]

        registros.append(registro)

    return pd.DataFrame(registros)


def contar_movimentacoes_categorizadas():
    """Retorna a quantidade de movimentações pendentes e categorizadas."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE categoria_id IS NULL
                ) AS pendentes,
                COUNT(*) FILTER (
                    WHERE categoria_id IS NOT NULL
                ) AS categorizadas
            FROM movimentacoes;
        """))

        return dict(resultado.mappings().one())


def atualizar_categoria_manual(movimentacao_id, categoria_id):
    """Salva manualmente a categoria de uma movimentação."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE movimentacoes
                SET categoria_id = :categoria_id
                WHERE id = :movimentacao_id;
            """),
            {
                "movimentacao_id": movimentacao_id,
                "categoria_id": categoria_id,
            },
        )

        return resultado.rowcount > 0


def atualizar_categorias_movimentacoes(df):
    registros = []

    for _, linha in df.iterrows():
        movimentacao_id = linha.get("movimentacao_id")
        categoria_id = linha.get("categoria_id")

        if pd.notna(movimentacao_id) and pd.notna(categoria_id):
            registros.append({
                "movimentacao_id": int(movimentacao_id),
                "categoria_id": int(categoria_id),
            })

    if not registros:
        return

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE movimentacoes
                SET categoria_id = :categoria_id
                WHERE id = :movimentacao_id
                AND categoria_id IS NULL;
            """),
            registros,
        )


def editar_categoria_movimentacao(movimentacao_id, categoria_id):
    """Atualiza a categoria de uma movimentação específica."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE movimentacoes
                SET categoria_id = :categoria_id
                WHERE id = :movimentacao_id;
            """),
            {
                "movimentacao_id": movimentacao_id,
                "categoria_id": categoria_id,
            }
        )

        return resultado.rowcount > 0
