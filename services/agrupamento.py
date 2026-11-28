
import re
import unicodedata

import pandas as pd
from rapidfuzz import fuzz


def normalizar_texto(texto):
    """
    Padroniza o texto para facilitar a comparação.
    """
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def agrupar_movimentacoes_similares(
    movimentacoes,
    limite_similaridade=85,
):
    """
    Agrupa movimentações com descrições iguais ou semelhantes.

    A comparação considera somente a descrição, não o valor.
    """

    grupos = []

    for _, linha in movimentacoes.iterrows():

        descricao_original = linha.get("Detalhes", "")
        descricao_normalizada = normalizar_texto(
            descricao_original
        )

        if not descricao_normalizada:
            continue

        grupo_encontrado = None
        melhor_similaridade = 0

        for grupo in grupos:

            similaridade = fuzz.ratio(
                descricao_normalizada,
                grupo["descricao_normalizada"],
            )

            if similaridade > melhor_similaridade:
                melhor_similaridade = similaridade
                grupo_encontrado = grupo

        if (
            grupo_encontrado is not None
            and melhor_similaridade >= limite_similaridade
        ):
            grupo_encontrado["movimentacoes"].append(
                linha.to_dict()
            )

        else:
            grupos.append({
                "descricao": descricao_original,
                "descricao_normalizada": descricao_normalizada,
                "movimentacoes": [linha.to_dict()],
            })

    # Mantém somente grupos com duas ou mais movimentações.
    grupos = [
        grupo
        for grupo in grupos
        if len(grupo["movimentacoes"]) >= 2
    ]

    return grupos
