
from sqlalchemy import text
from api.connection import get_connection


def testar_conexao():
    try:
        with get_connection() as connection:
            resultado = connection.execute(
                text("""
                    SELECT
                        version(),
                        current_database(),
                        current_user;
                """)
            ).fetchone()

            return {
                "status": "Conectado",
                "versao": resultado[0],
                "banco": resultado[1],
                "usuario": resultado[2],
            }

    except Exception as erro:
        return {
            "status": "Erro",
            "mensagem": str(erro),
        }
