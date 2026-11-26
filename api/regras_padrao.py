
from sqlalchemy import text
from api.connection import engine


def criar_regras_padrao():
    """Cadastra as palavras-chave padrão do sistema."""

    regras_padrao = {
        "Alimentação": [
            "IFOOD",
            "UBER EATS",
            "RAPPI",
            "RESTAURANTE",
            "LANCHONETE",
            "PIZZARIA",
            "BURGER KING",
            "MCDONALDS",
            "SUBWAY",
            "HABIBS",
        ],

        "Supermercado": [
            "CARREFOUR",
            "ASSAI",
            "ATACADAO",
            "SUPERMERCADO",
            "MERCADO",
            "BIG BOX",
            "PAO DE ACUCAR",
            "EXTRA",
            "DIA SUPERMERCADO",
            "TATICO",
        ],

        "Transporte": [
            "UBER TRIP",
            "99APP",
            "99POP",
            "POSTO",
            "ABASTECIMENTO",
            "SHELL",
            "IPIRANGA",
            "BRB MOBILIDADE",
            "SEM PARAR",
            "ESTACIONAMENTO",
        ],

        "Moradia": [
            "ALUGUEL",
            "CONDOMINIO",
            "ENERGIA",
            "NEOENERGIA",
            "EQUATORIAL",
            "CAESB",
            "SABESP",
            "ENEL",
            "COMPANHIA DE AGUA",
            "GAS ENCANADO",
        ],

        "Saúde": [
            "DROGASIL",
            "DROGARIA",
            "FARMACIA",
            "DROGA RAIA",
            "PAGUE MENOS",
            "PANVEL",
            "HOSPITAL",
            "CLINICA",
            "LABORATORIO",
            "UNIMED",
        ],

        "Educação": [
            "UDEMY",
            "COURSERA",
            "ALURA",
            "SENAC",
            "SENAI",
            "UNIVERSIDADE",
            "FACULDADE",
            "ESCOLA",
            "LIVRARIA",
            "CURSO",
        ],

        "Lazer": [
            "STEAM",
            "PLAYSTATION",
            "XBOX",
            "CINEMA",
            "INGRESSO",
            "SYMPLA",
            "EVENTIM",
            "PARQUE",
            "BOLICHE",
            "TEATRO",
        ],

        "Compras": [
            "AMAZON",
            "MERCADO LIVRE",
            "SHOPEE",
            "MAGALU",
            "SHEIN",
            "ALIEXPRESS",
            "RENNER",
            "RIACHUELO",
            "CENTAURO",
            "LOJAS AMERICANAS",
        ],

        "Assinaturas": [
            "NETFLIX",
            "DISNEY PLUS",
            "HBO MAX",
            "PRIME VIDEO",
            "YOUTUBE PREMIUM",
            "GLOBOPLAY",
            "APPLE COM BILL",
            "ICLOUD",
            "SPOTIFY",
            "MICROSOFT 365",
        ],

        "Transferências recebidas": [
            "PIX RECEBIDO",
            "TED RECEBIDA",
            "DOC RECEBIDO",
            "TRANSFERENCIA RECEBIDA",
            "TRANSF RECEBIDA",
            "CREDITO PIX",
            "PIX CREDITO",
            "DEPOSITO RECEBIDO",
            "DEPOSITO EM CONTA",
            "RECEBIMENTO PIX",
        ],

        "Transferências enviadas": [
            "PIX ENVIADO",
            "TED ENVIADA",
            "DOC ENVIADO",
            "TRANSFERENCIA ENVIADA",
            "TRANSF ENVIADA",
            "PAGAMENTO PIX",
            "PIX REALIZADO",
            "TRANSFERENCIA REALIZADA",
            "ENVIO PIX",
            "PIX PARA",
        ],
    }

    with engine.begin() as connection:

        for categoria, palavras in regras_padrao.items():

            for palavra in palavras:

                connection.execute(
                    text("""
                        INSERT INTO regras_categorizacao_padrao (
                            categoria,
                            palavra_chave
                        )
                        VALUES (
                            :categoria,
                            :palavra_chave
                        )
                        ON CONFLICT (
                            categoria,
                            palavra_chave
                        )
                        DO NOTHING
                    """),
                    {
                        "categoria": categoria,
                        "palavra_chave": palavra,
                    }
                )


def listar_regras_padrao():
    """Retorna todas as regras padrão ativas."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    categoria,
                    palavra_chave
                FROM regras_categorizacao_padrao
                WHERE ativo = TRUE
            """)
        )

        return [
            dict(regra)
            for regra in resultado.mappings().all()
        ]
