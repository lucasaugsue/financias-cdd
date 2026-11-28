
from sqlalchemy import text
from api.connection import engine


def criar_regras_padrao():
    """Cadastra as palavras-chave padrão do sistema."""

    regras_padrao = {
        "Alimentação": [
            # Regras existentes
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

            # Novas regras
            "KONI",
            "PANIFICADORA",
            "PANIF CASTANHEIRAS",
            "CACAU SHOW",
            "MC DONALS",
            "SEU JOACA FAST FOOD",
            "OUTBACK",
            "MADERO",
            "COCO BAMBU",
            "GIRAFFAS",
            "SPOLETO",
            "KFC",
            "DOMINOS",
            "PIZZA HUT",
            "STARBUCKS",
            "BOSTON BAKERY",
            "DONUTS",
        ],

        "Supermercado": [
            # Regras existentes
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

            # Novas regras
            "PRIME CARNES",
            "SUPERMERCADOS BH",
            "GPA",
            "FORT ATACADISTA",
            "SAM'S CLUB",
            "OBRAMAX",
            "COMPER",
            "OBa HORTIFRUTI",
            "HORTIFRUTI",
            "MIX MATEUS",
        ],

        "Transporte": [
            # Regras existentes
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

            # Novas regras
            "CASCOL COMBUSTIVEIS",
            "AUTO POSTO FENIX",
            "ESTAPAR",
            "INDIGO",
            "ZUL DIGITAL",
            "VIA FACIL",
            "CONCESSIONARIA",
            "PEDAGIO",
            "RECARGA BRB MOBILIDADE",
        ],

        "Moradia": [
            # Regras existentes
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

            # Novas regras
            "CEB",
            "SANEAGO",
            "COPASA",
            "SANEPAR",
            "COMGAS",
            "ULTRAGAZ",
            "NACIONAL GAS",
            "IPTU",
            "TAXA CONDOMINIAL",
        ],

        "Saúde": [
            # Regras existentes
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

            # Novas regras
            "DROGAFUJI",
            "INSTITUTO ODONTOLOGIC",
            "DROGARIA ROSARIO",
            "DROGARIA VENANCIO",
            "PACHECO",
            "ULTRAFARMA",
            "DROGARIA SAO PAULO",
            "ODONTO",
            "ODONTOLOGIA",
            "FLEURY",
            "DASA",
            "SABIN",
            "EXAME LABORATORIO",
        ],

        "Educação": [
            # Regras existentes
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

            # Novas regras
            "FG PAPELARIA",
            "GRAN CENTRO UNIVERSITARIO",
            "ESTACIO",
            "UNIP",
            "ANHANGUERA",
            "UNINTER",
            "DESCOMPLICA",
            "KULTIVI",
            "DOMESTIKA",
            "SKILLSHARE",
            "PAPELARIA",
        ],

        "Lazer": [
            # Regras existentes
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

            # Novas regras
            "PLAY BOWLING",
            "CINEMARK",
            "KINOPLEX",
            "UCI CINEMAS",
            "INGRESSO.COM",
            "TICKETMASTER",
            "HOT PARK",
            "BETO CARRERO",
            "PARQUE AQUATICO",
            "ZOOLOGICO",
        ],

        "Compras": [
            # Regras existentes
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

            # Novas regras
            "AMERICANAS",
            "CASAS BAHIA",
            "PONTO FRIO",
            "FAST SHOP",
            "KALUNGA",
            "DECATHLON",
            "ZARA",
            "C&A",
            "MARISA",
            "PETZ",
            "COBASI",
            "FLORICULTURA",
            "MULTIDISPLAY",
        ],

        "Assinaturas": [
            # Regras existentes
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

            # Novas regras
            "GOOGLE ONE",
            "GOOGLE STORAGE",
            "CRUNCHYROLL",
            "PARAMOUNT PLUS",
            "DEEZER",
            "CANVA",
            "ADOBE",
            "DROPBOX",
            "GOOGLE WORKSPACE",
            "CHATGPT",
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
