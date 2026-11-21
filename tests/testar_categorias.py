
from api.categorias import (
    listar_categorias,
    cadastrar_regra_categorizacao,
    listar_regras_categorizacao,
)

categorias = listar_categorias()

regras_novas = {
    "Alimentação": [
        "PANIF",
        "ROYAL BURGER",
        "IFOOD",
        "KONI",
        "PIZZA CESAR",
    ],
    "Supermercado": [
        "CARREFOUR",
    ],
    "Saúde": [
        "FARMACIA",
        "DROGARIA",
    ],
    "Transporte": [
        "BRB MOBILIDADE",
        "BANCO VOLKSWAGEN",
    ],
    "Compras": [
        "MARKETPLACE",
    ],
    "Igreja": [
        "IGREJA",
    ],
    "Compras": [
        "PAGSEGURO",
        "PAY2ALL",
        "GIFT CARDS",
    ],
    "Saúde": [
        "OTORRINOLARI",
    ],
    "Alimentação": [
        "BURGUE",
        "LIFEBOX",
    ],
    "Panificadora": [
        "PAES",
        "BALTAZARJOSE",
    ],
    "Supermercado": [
        "DONA",
    ],
    "Celular": [
        "MULTIDISPLAY COMERCIO",
    ],
    "Devoluções": [
        "ENVIO DEVOLVIDO",
    ],
}

for categoria_nome, palavras in regras_novas.items():
    categoria = next(
        (
            item for item in categorias
            if item["categoria"] == categoria_nome
        ),
        None,
    )

    if categoria:
        for palavra in palavras:
            resultado = cadastrar_regra_categorizacao(
                palavra,
                categoria["id"],
            )

            if resultado:
                print(f"Cadastrada: {palavra} -> {categoria_nome}")

print("\nRegras cadastradas:")
for regra in listar_regras_categorizacao():
    print(f"{regra['palavra_chave']} -> {regra['categoria']}")
