
from sqlalchemy import text

from api.connection import engine


def criar_categorias_padrao(usuario_id):
    """Cria as categorias iniciais para um usuário."""

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
                INSERT INTO categorias (
                    usuario_id,
                    categoria,
                    finalidade
                )
                VALUES (
                    :usuario_id,
                    :categoria,
                    :finalidade
                )
                ON CONFLICT DO NOTHING;
            """),
            [
                {
                    "usuario_id": usuario_id,
                    **categoria
                }
                for categoria in categorias
            ]
        )


def listar_categorias(usuario_id):
    """Retorna somente as categorias do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT id, categoria, finalidade
                FROM categorias
                WHERE usuario_id = :usuario_id
                ORDER BY categoria;
            """),
            {"usuario_id": usuario_id}
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]


def cadastrar_categoria(categoria, finalidade, usuario_id):
    """Cadastra uma nova categoria para o usuário."""

    categoria = categoria.strip()

    if not categoria:
        return "invalida"

    if finalidade not in ["Receita", "Despesa", "Ambas"]:
        return "invalida"

    with engine.begin() as connection:

        existente = connection.execute(
            text("""
                SELECT id
                FROM categorias
                WHERE LOWER(TRIM(categoria)) =
                    LOWER(TRIM(:categoria))
                AND usuario_id = :usuario_id;
            """),
            {
                "categoria": categoria,
                "usuario_id": usuario_id
            }
        ).first()

        if existente:
            return "existente"

        connection.execute(
            text("""
                INSERT INTO categorias (
                    usuario_id,
                    categoria,
                    finalidade
                )
                VALUES (
                    :usuario_id,
                    :categoria,
                    :finalidade
                );
            """),
            {
                "usuario_id": usuario_id,
                "categoria": categoria,
                "finalidade": finalidade,
            }
        )

    return "criada"


def cadastrar_regra_categorizacao(
    palavra_chave,
    categoria_id,
    usuario_id
):
    """Cadastra uma regra em uma categoria do próprio usuário."""

    palavra_chave = palavra_chave.strip().upper()

    if not palavra_chave:
        return False

    with engine.begin() as connection:

        categoria = connection.execute(
            text("""
                SELECT id
                FROM categorias
                WHERE id = :categoria_id
                  AND usuario_id = :usuario_id;
            """),
            {
                "categoria_id": categoria_id,
                "usuario_id": usuario_id
            }
        ).first()

        if not categoria:
            return False

        resultado = connection.execute(
            text("""
                INSERT INTO regras_categorizacao (
                    usuario_id,
                    palavra_chave,
                    categoria_id
                )
                VALUES (
                    :usuario_id,
                    :palavra_chave,
                    :categoria_id
                )
                ON CONFLICT DO NOTHING;
            """),
            {
                "usuario_id": usuario_id,
                "palavra_chave": palavra_chave,
                "categoria_id": categoria_id,
            }
        )

        return resultado.rowcount > 0


def verificar_regra_categorizacao(
    palavra_chave,
    categoria_id,
    usuario_id
):
    """Verifica regras existentes somente na conta do usuário."""

    palavra_chave = palavra_chave.strip().upper()

    if not palavra_chave:
        return {"status": "invalida"}

    with engine.connect() as connection:

        categoria = connection.execute(
            text("""
                SELECT id
                FROM categorias
                WHERE id = :categoria_id
                  AND usuario_id = :usuario_id;
            """),
            {
                "categoria_id": categoria_id,
                "usuario_id": usuario_id
            }
        ).first()

        if not categoria:
            return {"status": "invalida"}

        resultado = connection.execute(
            text("""
                SELECT
                    r.categoria_id,
                    c.categoria
                FROM regras_categorizacao r
                INNER JOIN categorias c
                    ON c.id = r.categoria_id
                WHERE LOWER(TRIM(r.palavra_chave)) =
                    LOWER(TRIM(:palavra_chave))
                  AND r.usuario_id = :usuario_id
                  AND r.ativo = TRUE;
            """),
            {
                "palavra_chave": palavra_chave,
                "usuario_id": usuario_id
            }
        )

        registros = resultado.mappings().all()

    conflitos = [
        registro["categoria"]
        for registro in registros
        if registro["categoria_id"] != categoria_id
    ]

    if conflitos:
        return {
            "status": "conflito",
            "categorias": conflitos,
        }

    if registros:
        return {"status": "existente"}

    return {"status": "nova"}


def editar_regra_categorizacao(
    regra_id,
    nova_palavra_chave,
    usuario_id
):
    """Edita uma regra pertencente ao usuário."""

    nova_palavra_chave = nova_palavra_chave.strip().upper()

    if not nova_palavra_chave:
        return False

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE regras_categorizacao
                SET palavra_chave = :palavra_chave
                WHERE id = :regra_id
                  AND usuario_id = :usuario_id
                  AND ativo = TRUE
                  AND NOT EXISTS (
                      SELECT 1
                      FROM regras_categorizacao outra
                      WHERE outra.id <> :regra_id
                        AND outra.usuario_id = :usuario_id
                        AND outra.categoria_id =
                            regras_categorizacao.categoria_id
                        AND outra.ativo = TRUE
                        AND LOWER(TRIM(outra.palavra_chave)) =
                            LOWER(TRIM(:palavra_chave))
                  );
            """),
            {
                "regra_id": regra_id,
                "palavra_chave": nova_palavra_chave,
                "usuario_id": usuario_id,
            }
        )

        return resultado.rowcount > 0


def excluir_regra_categorizacao(regra_id, usuario_id):
    """Desativa uma regra pertencente ao usuário."""

    with engine.begin() as connection:
        resultado = connection.execute(
            text("""
                UPDATE regras_categorizacao
                SET ativo = FALSE
                WHERE id = :regra_id
                  AND usuario_id = :usuario_id
                  AND ativo = TRUE;
            """),
            {
                "regra_id": regra_id,
                "usuario_id": usuario_id
            }
        )

        return resultado.rowcount > 0


def listar_regras_categorizacao(usuario_id):
    """Retorna somente as regras ativas do usuário."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    r.id,
                    r.palavra_chave,
                    r.categoria_id,
                    r.criado_em,
                    c.categoria,
                    c.finalidade
                FROM regras_categorizacao r
                INNER JOIN categorias c
                    ON c.id = r.categoria_id
                WHERE r.ativo = TRUE
                  AND r.usuario_id = :usuario_id
                  AND c.usuario_id = :usuario_id
                ORDER BY r.id;
            """),
            {"usuario_id": usuario_id}
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]
