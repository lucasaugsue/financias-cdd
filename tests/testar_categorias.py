
from api.categorias import (
    listar_categorias,
    cadastrar_regra_categorizacao,
    listar_regras_categorizacao,
)


def executar():

    # Identifica o usuário que receberá as regras
    try:
        usuario_id = int(input("Informe o ID do usuário: "))
    except ValueError:
        print("ID inválido.")
        return

    if usuario_id <= 0:
        print("O ID deve ser maior que zero.")
        return

    categorias = listar_categorias(usuario_id)

    regras_novas = [
        ("Alimentação", [
            "PANIF",
            "ROYAL BURGER",
            "IFOOD",
            "KONI",
            "PIZZA CESAR",
            "BURGUE",
            "LIFEBOX",
        ]),
        ("Supermercado", [
            "CARREFOUR",
            "DONA",
        ]),
        ("Saúde", [
            "FARMACIA",
            "DROGARIA",
            "OTORRINOLARI",
        ]),
        ("Transporte", [
            "BRB MOBILIDADE",
            "BANCO VOLKSWAGEN",
        ]),
        ("Compras", [
            "MARKETPLACE",
            "PAGSEGURO",
            "PAY2ALL",
            "GIFT CARDS",
        ]),
        ("Igreja", [
            "IGREJA",
        ]),
        ("Panificadora", [
            "PAES",
            "BALTAZARJOSE",
        ]),
        ("Celular", [
            "MULTIDISPLAY COMERCIO",
        ]),
        ("Devoluções", [
            "ENVIO DEVOLVIDO",
        ]),
    ]

    # Cadastra as regras
    for categoria_nome, palavras in regras_novas:

        categoria = next(
            (
                item for item in categorias
                if item["categoria"] == categoria_nome
            ),
            None,
        )

        if not categoria:
            print(f"Categoria não encontrada: {categoria_nome}")
            continue

        for palavra in palavras:

            resultado = cadastrar_regra_categorizacao(
                palavra,
                categoria["id"],
                usuario_id,
            )

            if resultado:
                print(f"Cadastrada: {palavra} -> {categoria_nome}")
            else:
                print(f"Não cadastrada (já existe?): {palavra}")

    # Exibe as regras do usuário
    print("\nRegras cadastradas:")

    for regra in listar_regras_categorizacao(usuario_id):
        print(f"{regra['palavra_chave']} -> {regra['categoria']}")


if __name__ == "__main__":
    executar()
