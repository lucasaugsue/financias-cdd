
import json

import pandas as pd
from sqlalchemy import text

from api.connection import engine


def criar_tabelas():
    """Cria e atualiza a estrutura das tabelas do banco."""

    with engine.begin() as connection:

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS extratos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                nome_arquivo TEXT NOT NULL,
                banco_origem TEXT NOT NULL,
                hash_arquivo VARCHAR(64) NOT NULL,
                quantidade_registros INTEGER NOT NULL DEFAULT 0,
                criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                categoria TEXT NOT NULL,
                finalidade TEXT NOT NULL
                    CHECK (finalidade IN ('Receita', 'Despesa', 'Ambas'))
            );
        """))

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

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS regras_categorizacao (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                palavra_chave TEXT NOT NULL,
                categoria_id INTEGER NOT NULL
                    REFERENCES categorias(id) ON DELETE CASCADE,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (TRIM(palavra_chave) <> '')
            );
        """))

        connection.execute(text("""
            ALTER TABLE extratos
            ADD COLUMN IF NOT EXISTS usuario_id INTEGER
            REFERENCES usuarios(id);
        """))

        connection.execute(text("""
            ALTER TABLE categorias
            ADD COLUMN IF NOT EXISTS usuario_id INTEGER
            REFERENCES usuarios(id);
        """))

        connection.execute(text("""
            ALTER TABLE regras_categorizacao
            ADD COLUMN IF NOT EXISTS usuario_id INTEGER
            REFERENCES usuarios(id);
        """))

        connection.execute(text("""
            ALTER TABLE movimentacoes
            ADD COLUMN IF NOT EXISTS categoria_id INTEGER;
        """))

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

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_extratos_usuario_hash
            ON extratos (usuario_id, hash_arquivo)
            WHERE usuario_id IS NOT NULL;
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_usuario_nome
            ON categorias (usuario_id, LOWER(TRIM(categoria)))
            WHERE usuario_id IS NOT NULL;
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_regra_palavra_categoria
            ON regras_categorizacao (
                LOWER(TRIM(palavra_chave)),
                categoria_id
            )
            WHERE ativo = TRUE;
        """))


def listar_extratos(usuario_id):
    """Retorna somente os extratos do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    id,
                    nome_arquivo,
                    banco_origem,
                    quantidade_registros,
                    criado_em
                FROM extratos
                WHERE usuario_id = :usuario_id
                ORDER BY criado_em DESC;
            """),
            {"usuario_id": usuario_id}
        )

        return [dict(linha) for linha in resultado.mappings().all()]


def buscar_movimentacoes(extrato_id, usuario_id):
    """Busca movimentações de um extrato pertencente ao usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT m.id, m.extrato_id, m.dados
                FROM movimentacoes m
                INNER JOIN extratos e
                    ON e.id = m.extrato_id
                WHERE m.extrato_id = :extrato_id
                  AND e.usuario_id = :usuario_id
                ORDER BY m.id;
            """),
            {
                "extrato_id": extrato_id,
                "usuario_id": usuario_id
            }
        )

        registros = resultado.mappings().all()

    return pd.DataFrame([dict(registro["dados"]) for registro in registros])


def salvar_extrato(nome_arquivo, banco_origem, hash_arquivo, df, usuario_id):
    """Salva um extrato e suas movimentações para um usuário."""

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
                WHERE hash_arquivo = :hash_arquivo
                  AND usuario_id = :usuario_id;
            """),
            {
                "hash_arquivo": hash_arquivo,
                "usuario_id": usuario_id
            }
        ).first()

        if duplicado:
            raise ValueError("Este arquivo já foi importado.")

        resultado = connection.execute(
            text("""
                INSERT INTO extratos (
                    usuario_id,
                    nome_arquivo,
                    banco_origem,
                    hash_arquivo,
                    quantidade_registros
                )
                VALUES (
                    :usuario_id,
                    :nome,
                    :banco,
                    :hash,
                    :quantidade
                )
                RETURNING id;
            """),
            {
                "usuario_id": usuario_id,
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


def atualizar_extrato(extrato_id, df, usuario_id):
    """Substitui as movimentações de um extrato do usuário."""

    registros = json.loads(
        df.to_json(
            orient="records",
            date_format="iso",
            force_ascii=False
        )
    )

    with engine.begin() as connection:

        existe = connection.execute(
            text("""
                SELECT id
                FROM extratos
                WHERE id = :extrato_id
                  AND usuario_id = :usuario_id;
            """),
            {
                "extrato_id": extrato_id,
                "usuario_id": usuario_id
            }
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
                WHERE id = :extrato_id
                  AND usuario_id = :usuario_id;
            """),
            {
                "quantidade": len(registros),
                "extrato_id": extrato_id,
                "usuario_id": usuario_id
            }
        )


def excluir_extrato(extrato_id, usuario_id):
    """Exclui somente um extrato pertencente ao usuário."""

    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM extratos
                WHERE id = :extrato_id
                  AND usuario_id = :usuario_id;
            """),
            {
                "extrato_id": extrato_id,
                "usuario_id": usuario_id
            }
        )


def listar_movimentacoes_consolidadas(usuario_id):
    """Retorna movimentações dos extratos do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
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
                WHERE e.usuario_id = :usuario_id
                ORDER BY e.banco_origem, m.id;
            """),
            {"usuario_id": usuario_id}
        )

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


def listar_movimentacoes_pendentes(usuario_id):
    """Retorna movimentações sem categoria do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    m.id AS movimentacao_id,
                    m.extrato_id,
                    e.banco_origem,
                    m.dados
                FROM movimentacoes m
                INNER JOIN extratos e
                    ON e.id = m.extrato_id
                WHERE m.categoria_id IS NULL
                  AND e.usuario_id = :usuario_id
                ORDER BY m.id;
            """),
            {"usuario_id": usuario_id}
        )

        linhas = resultado.mappings().all()

    registros = []

    for linha in linhas:
        registro = dict(linha["dados"])

        registro["movimentacao_id"] = linha["movimentacao_id"]
        registro["extrato_id"] = linha["extrato_id"]
        registro["banco_origem"] = linha["banco_origem"]

        registros.append(registro)

    return pd.DataFrame(registros)


def contar_movimentacoes_categorizadas(usuario_id):
    """Conta movimentações pendentes e categorizadas do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE m.categoria_id IS NULL
                    ) AS pendentes,
                    COUNT(*) FILTER (
                        WHERE m.categoria_id IS NOT NULL
                    ) AS categorizadas
                FROM movimentacoes m
                INNER JOIN extratos e
                    ON e.id = m.extrato_id
                WHERE e.usuario_id = :usuario_id;
            """),
            {"usuario_id": usuario_id}
        )

        return dict(resultado.mappings().one())


def atualizar_categoria_manual(movimentacao_id, categoria_id, usuario_id):
    """Classifica uma movimentação pertencente ao usuário."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE movimentacoes m
                SET categoria_id = :categoria_id
                WHERE m.id = :movimentacao_id

                  AND EXISTS (
                      SELECT 1
                      FROM extratos e
                      WHERE e.id = m.extrato_id
                        AND e.usuario_id = :usuario_id
                  )

                  AND EXISTS (
                      SELECT 1
                      FROM categorias c
                      WHERE c.id = :categoria_id
                        AND c.usuario_id = :usuario_id
                  );
            """),
            {
                "movimentacao_id": movimentacao_id,
                "categoria_id": categoria_id,
                "usuario_id": usuario_id
            }
        )

        return resultado.rowcount > 0


def atualizar_categorias_movimentacoes(df, usuario_id):
    """Atualiza categorias em lote somente nas movimentações do usuário."""

    registros = []

    for _, linha in df.iterrows():
        movimentacao_id = linha.get("movimentacao_id")
        categoria_id = linha.get("categoria_id")

        if pd.notna(movimentacao_id) and pd.notna(categoria_id):
            registros.append({
                "movimentacao_id": int(movimentacao_id),
                "categoria_id": int(categoria_id),
                "usuario_id": usuario_id
            })

    if not registros:
        return

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE movimentacoes m
                SET categoria_id = :categoria_id
                WHERE m.id = :movimentacao_id
                  AND m.categoria_id IS NULL

                  AND EXISTS (
                      SELECT 1
                      FROM extratos e
                      WHERE e.id = m.extrato_id
                        AND e.usuario_id = :usuario_id
                  )

                  AND EXISTS (
                      SELECT 1
                      FROM categorias c
                      WHERE c.id = :categoria_id
                        AND c.usuario_id = :usuario_id
                  );
            """),
            registros
        )


def editar_categoria_movimentacao(movimentacao_id, categoria_id, usuario_id):
    """Atualiza a categoria de uma movimentação do usuário."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE movimentacoes m
                SET categoria_id = :categoria_id
                WHERE m.id = :movimentacao_id

                  AND EXISTS (
                      SELECT 1
                      FROM extratos e
                      WHERE e.id = m.extrato_id
                        AND e.usuario_id = :usuario_id
                  )

                  AND EXISTS (
                      SELECT 1
                      FROM categorias c
                      WHERE c.id = :categoria_id
                        AND c.usuario_id = :usuario_id
                  );
            """),
            {
                "movimentacao_id": movimentacao_id,
                "categoria_id": categoria_id,
                "usuario_id": usuario_id
            }
        )

        return resultado.rowcount > 0


def contar_pendentes_por_detalhes(
    detalhes,
    usuario_id,
    movimentacao_id,
):
    """Conta outras movimentações pendentes com o mesmo detalhamento."""

    if not detalhes or not str(detalhes).strip():
        return 0

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM movimentacoes m
                INNER JOIN extratos e
                    ON e.id = m.extrato_id
                WHERE e.usuario_id = :usuario_id
                  AND m.categoria_id IS NULL
                  AND m.id <> :movimentacao_id
                  AND LOWER(TRIM(
                      COALESCE(
                          m.dados ->> 'Detalhes',
                          m.dados ->> 'detalhes',
                          ''
                      )
                  )) = LOWER(TRIM(:detalhes));
            """),
            {
                "usuario_id": usuario_id,
                "movimentacao_id": movimentacao_id,
                "detalhes": str(detalhes).strip(),
            }
        )

        return resultado.scalar_one()


def atualizar_categoria_por_detalhes(
    detalhes,
    categoria_id,
    usuario_id,
    movimentacao_id,
):
    """Classifica outras movimentações pendentes com o mesmo detalhamento."""

    if not detalhes or not str(detalhes).strip():
        return 0

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE movimentacoes m
                SET categoria_id = :categoria_id
                FROM extratos e
                WHERE e.id = m.extrato_id
                  AND e.usuario_id = :usuario_id
                  AND m.categoria_id IS NULL
                  AND m.id <> :movimentacao_id
                  AND LOWER(TRIM(
                      COALESCE(
                          m.dados ->> 'Detalhes',
                          m.dados ->> 'detalhes',
                          ''
                      )
                  )) = LOWER(TRIM(:detalhes))
                  AND EXISTS (
                      SELECT 1
                      FROM categorias c
                      WHERE c.id = :categoria_id
                        AND c.usuario_id = :usuario_id
                  );
            """),
            {
                "usuario_id": usuario_id,
                "movimentacao_id": movimentacao_id,
                "categoria_id": categoria_id,
                "detalhes": str(detalhes).strip(),
            }
        )

        return resultado.rowcount