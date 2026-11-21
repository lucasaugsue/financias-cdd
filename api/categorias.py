from sqlalchemy import text

from api.connection import engine

def criar_categorias_padrao():
    """Cadastra as categorias iniciais, caso ainda não existam."""

    categorias = [
        {"categoria": "Salário", "finalidade": "Receita"},
        {"categoria": "Rendimentos", "finalidade": "Receita"},
        {"categoria": "Transferências recebidas", "finalidade": "Receita"},
        {"categoria": "Alimentação", "finalidade": "Despesa"},
        {"categoria": "Supermercado", "finalidade": "Despesa"},
        {"categoria": "Transporte", "finalidade": "Despesa"},
        {"categoria": "Moradia", "finalidade": "Despesa"},
        {"categoria": "Saúde", "finalidade": "Despesa"},
        {"categoria": "Educação", "finalidade": "Despesa"},
        {"categoria": "Lazer", "finalidade": "Despesa"},
        {"categoria": "Assinaturas", "finalidade": "Despesa"},
        {"categoria": "Compras", "finalidade": "Despesa"},
        {"categoria": "Tarifas e taxas", "finalidade": "Despesa"},
        {"categoria": "Impostos", "finalidade": "Despesa"},
        {"categoria": "Transferências enviadas", "finalidade": "Despesa"},
        {"categoria": "Outros", "finalidade": "Ambas"},
        {"categoria": "Igreja", "finalidade": "Despesa"},
        {"categoria": "Panificadora", "finalidade": "Despesa"},
        {"categoria": "Celular", "finalidade": "Despesa"},
        {"categoria": "Devoluções", "finalidade": "Receita"},
    ]

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO categorias (categoria, finalidade)
                VALUES (:categoria, :finalidade)
                ON CONFLICT (categoria) DO NOTHING;
            """),
            categorias
        )


def listar_categorias():
    """Retorna todas as categorias cadastradas."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT id, categoria, finalidade
            FROM categorias
            ORDER BY categoria;
        """))

        return [dict(linha) for linha in resultado.mappings().all()]


def cadastrar_regra_categorizacao(palavra_chave, categoria_id):
    """Cadastra uma palavra-chave associada a uma categoria."""

    palavra_chave = palavra_chave.strip()

    if not palavra_chave:
        return False

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                INSERT INTO regras_categorizacao (
                    palavra_chave,
                    categoria_id
                )
                VALUES (
                    :palavra_chave,
                    :categoria_id
                )
                ON CONFLICT DO NOTHING;
            """),
            {
                "palavra_chave": palavra_chave,
                "categoria_id": categoria_id,
            }
        )

        return resultado.rowcount > 0


def editar_regra_categorizacao(regra_id, nova_palavra_chave):
    """Altera uma palavra-chave sem permitir duplicidade na categoria."""

    nova_palavra_chave = nova_palavra_chave.strip()

    if not nova_palavra_chave:
        return False

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE regras_categorizacao
                SET palavra_chave = :palavra_chave
                WHERE id = :regra_id
                AND ativo = TRUE
                AND NOT EXISTS (
                    SELECT 1
                    FROM regras_categorizacao outra
                    WHERE outra.id <> :regra_id
                    AND outra.categoria_id = regras_categorizacao.categoria_id
                    AND LOWER(TRIM(outra.palavra_chave)) =
                        LOWER(TRIM(:palavra_chave))
                );
            """),
            {
                "regra_id": regra_id,
                "palavra_chave": nova_palavra_chave,
            }
        )

        return resultado.rowcount > 0


def excluir_regra_categorizacao(regra_id):
    """Desativa uma palavra-chave para que não seja mais utilizada."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE regras_categorizacao
                SET ativo = FALSE
                WHERE id = :regra_id
                AND ativo = TRUE;
            """),
            {"regra_id": regra_id}
        )

        return resultado.rowcount > 0


def listar_regras_categorizacao():
    """Retorna todas as regras de categorização ativas."""

    with engine.connect() as connection:
        resultado = connection.execute(text("""
            SELECT
                r.id,
                r.palavra_chave,
                r.categoria_id,
                c.categoria,
                c.finalidade
            FROM regras_categorizacao r
            INNER JOIN categorias c
                ON c.id = r.categoria_id
            WHERE r.ativo = TRUE
            ORDER BY r.id;
        """))

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]
