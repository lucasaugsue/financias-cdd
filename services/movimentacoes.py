
import unicodedata
import pandas as pd

from api.regras_padrao import listar_regras_padrao

from api.categorias import (
    listar_regras_categorizacao,
    listar_categorias,
)


# ============================================================
# NORMALIZAÇÃO E IDENTIFICAÇÃO DE COLUNAS
# ============================================================

def normalizar_nome_coluna(nome):
    """Normaliza nomes de colunas, ignorando acentos e maiúsculas."""

    nome = str(nome).strip().casefold()
    nome = unicodedata.normalize("NFKD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    return " ".join(nome.split())


def obter_campo(linha, nomes):
    """Localiza um campo em uma linha usando nomes alternativos."""

    nomes_normalizados = {
        normalizar_nome_coluna(nome)
        for nome in nomes
    }

    for coluna in linha.index:

        if normalizar_nome_coluna(coluna) in nomes_normalizados:
            return linha[coluna]

    return None


def identificar_coluna_data(df):
    """Identifica a coluna que contém as datas das movimentações."""

    return next(
        (
            coluna for coluna in df.columns
            if normalizar_nome_coluna(coluna) in ["data", "date"]
        ),
        None,
    )


def identificar_coluna_tipo(df):
    """Identifica a coluna de tipo de lançamento."""

    return next(
        (
            coluna for coluna in df.columns
            if normalizar_nome_coluna(coluna) in [
                "tipo",
                "tipo lancamento",
                "tipo de lancamento",
                "natureza",
            ]
        ),
        None,
    )


def identificar_coluna_valor(df):
    """Identifica a coluna que contém os valores das movimentações."""

    return next(
        (
            coluna for coluna in df.columns
            if normalizar_nome_coluna(coluna) in [
                "valor",
                "amount",
                "brl",
            ]
        ),
        None,
    )


# ============================================================
# FORMATAÇÃO E PREPARAÇÃO DOS DADOS
# ============================================================

def formatar_texto(valor):
    """Converte valores ausentes em uma representação visual."""

    if valor is None or pd.isna(valor):
        return "—"

    return str(valor)


def preparar_tabela_movimentacoes(movimentacoes):

    if movimentacoes is None or movimentacoes.empty:
        return pd.DataFrame()

    registros = []

    for _, linha in movimentacoes.iterrows():

        data = obter_campo(
            linha,
            ["Data", "data"],
        )

        descricao = obter_campo(
            linha,
            ["Descrição", "Descricao", "description"],
        )

        detalhes = obter_campo(
            linha,
            ["Detalhes", "detalhes"],
        )

        lancamento = obter_campo(
            linha,
            ["Lançamento", "Lancamento", "lancamento"],
        )

        valor = obter_campo(
            linha,
            ["Valor", "valor", "Amount", "BRL"],
        )

        tipo = obter_campo(
            linha,
            ["Tipo", "tipo", "Tipo lançamento", "Tipo de lançamento"],
        )

        banco = obter_campo(
            linha,
            ["Banco", "banco", "banco_origem", "Banco origem"],
        )

        # Se o arquivo possui uma descrição única,
        # separa o nome da movimentação dos detalhes.
        if descricao is not None and not pd.isna(descricao):

            partes = str(descricao).split(" - ", 1)

            lancamento = partes[0].strip()

            detalhes = (
                partes[1].strip()
                if len(partes) > 1
                else "—"
            )

            lancamento_normalizado = lancamento.casefold()

            if lancamento_normalizado == "transferência enviada pelo pix":
                lancamento = "Transferência Pix"

            elif lancamento_normalizado == "compra no débito":
                lancamento = "Compra no débito"

        else:

            # Mantém os campos separados quando o banco
            # já fornece lançamento e detalhes individualmente.
            if lancamento is None or pd.isna(lancamento):
                lancamento = detalhes

        # Identifica entrada ou saída pelo sinal do valor.
        if tipo is None or pd.isna(tipo):

            if valor is not None and not pd.isna(valor):

                valor_numerico = converter_valor_monetario(valor)

                if valor_numerico is not None:
                    tipo = "Entrada" if valor_numerico > 0 else "Saída"

        registros.append({
            "Data": formatar_texto(data),
            "Detalhes": formatar_texto(detalhes),
            "Lançamento": formatar_texto(lancamento),
            "Valor": valor,
            "Tipo": formatar_texto(tipo),
            "Banco": formatar_texto(banco),
        })

    return pd.DataFrame(registros)


def preparar_movimentacoes(df):
    """Prepara os dados e identifica o tipo de lançamento."""

    df = df.copy()

    coluna_data = identificar_coluna_data(df)
    coluna_tipo = identificar_coluna_tipo(df)
    coluna_valor = identificar_coluna_valor(df)

    # Padroniza as datas.
    if coluna_data:
        df[coluna_data] = pd.to_datetime(
            df[coluna_data],
            errors="coerce",
            dayfirst=True,
        ).dt.date

    # Se não existir uma coluna de tipo, cria uma pelo valor.
    if not coluna_tipo or coluna_tipo not in df.columns:

        if not coluna_valor:
            raise ValueError(
                "Não foi possível identificar a coluna de valor."
            )

        coluna_tipo = "Tipo"

        df[coluna_tipo] = "Não identificado"

        valores = df[coluna_valor].apply(
            converter_valor_monetario
        )

        df.loc[valores > 0, coluna_tipo] = "Entrada"
        df.loc[valores < 0, coluna_tipo] = "Saída"
        df.loc[valores == 0, coluna_tipo] = "Neutro"

    else:
        # Normaliza os valores existentes na coluna de tipo.
        df[coluna_tipo] = (
            df[coluna_tipo]
            .astype(str)
            .str.strip()
            .str.casefold()
            .replace({
                "entrada": "Entrada",
                "saída": "Saída",
                "saida": "Saída",
            })
        )

        # Corrige registros sem tipo identificado.
        tipos_vazios = df[coluna_tipo].isin([
            "none",
            "nan",
            "",
            "não identificado",
        ])

        if coluna_valor:
            valores = df[coluna_valor].apply(
                converter_valor_monetario
            )

            df.loc[
                tipos_vazios & (valores > 0),
                coluna_tipo
            ] = "Entrada"

            df.loc[
                tipos_vazios & (valores < 0),
                coluna_tipo
            ] = "Saída"

            df.loc[
                tipos_vazios & (valores == 0),
                coluna_tipo
            ] = "Neutro"

    return df, coluna_data, coluna_tipo


# ============================================================
# CATEGORIZAÇÃO AUTOMÁTICA
# ============================================================

def categorizar_movimentacoes(df, usuario_id):
    """Categoriza usando regras personalizadas e padrão."""

    df = df.copy()

    coluna_detalhes = next(
        (
            coluna for coluna in df.columns
            if normalizar_nome_coluna(coluna)
            in ["detalhes", "descricao"]
        ),
        None,
    )

    coluna_lancamento = next(
        (
            coluna for coluna in df.columns
            if normalizar_nome_coluna(coluna)
            in ["lancamento"]
        ),
        None,
    )

    # Buscar categorias e regras
    categorias = listar_categorias(usuario_id)
    regras_usuario = listar_regras_categorizacao(usuario_id)
    regras_padrao = listar_regras_padrao()

    # Relacionar IDs das categorias do usuário aos nomes
    nomes_categorias = {
        categoria["id"]: categoria["categoria"]
        for categoria in categorias
    }

    # Relacionar nomes das categorias aos IDs do usuário
    ids_categorias = {
        normalizar_nome_coluna(categoria["categoria"]): categoria["id"]
        for categoria in categorias
    }

    # Preparar regras personalizadas
    regras = []

    for regra in regras_usuario:
        regras.append({
            "palavra_chave": regra["palavra_chave"],
            "categoria": regra["categoria"],
            "categoria_id": regra["categoria_id"],
            "prioridade": 1,
        })

    # Preparar regras padrão usando o ID da categoria do usuário
    for regra in regras_padrao:

        nome_categoria = normalizar_nome_coluna(regra["categoria"])

        categoria_id = ids_categorias.get(nome_categoria)

        if categoria_id is None:
            continue

        regras.append({
            "palavra_chave": regra["palavra_chave"],
            "categoria": regra["categoria"],
            "categoria_id": categoria_id,
            "prioridade": 2,
        })

    # Priorizar regras personalizadas e palavras mais específicas
    regras = sorted(
        regras,
        key=lambda regra: (
            regra["prioridade"],
            -len(regra["palavra_chave"].strip()),
        )
    )

    # Preservar categorias já existentes
    if "categoria_id" not in df.columns:
        df["categoria_id"] = None

    if "categoria" not in df.columns:
        df["categoria"] = None

    if "palavra_chave_identificada" not in df.columns:
        df["palavra_chave_identificada"] = None

    # Recuperar o nome das categorias já salvas
    for indice, movimentacao in df.iterrows():

        categoria_id = movimentacao["categoria_id"]

        if pd.notna(categoria_id):

            categoria_id = int(categoria_id)

            df.at[indice, "categoria_id"] = categoria_id

            df.at[indice, "categoria"] = nomes_categorias.get(
                categoria_id,
                movimentacao["categoria"],
            )

    # Categorizar somente movimentações pendentes
    for indice, movimentacao in df.iterrows():

        if pd.notna(movimentacao["categoria_id"]):
            continue

        textos = []

        for coluna in [coluna_detalhes, coluna_lancamento]:

            if coluna:

                valor = movimentacao[coluna]

                if pd.notna(valor):
                    textos.append(normalizar_nome_coluna(valor))

        texto_busca = " ".join(textos)

        for regra in regras:

            palavra = normalizar_nome_coluna(regra["palavra_chave"])

            if palavra and palavra in texto_busca:

                df.at[indice, "categoria_id"] = regra["categoria_id"]

                df.at[indice, "categoria"] = nomes_categorias.get(
                    regra["categoria_id"],
                    regra["categoria"],
                )

                df.at[indice, "palavra_chave_identificada"] = (
                    regra["palavra_chave"]
                )

                break

    return df


# ============================================================
# FILTROS
# ============================================================

def listar_periodos_disponiveis(df, coluna_data):
    """Retorna os meses/anos que possuem movimentações cadastradas."""

    if not coluna_data or coluna_data not in df.columns:
        return []

    datas = pd.to_datetime(
        df[coluna_data],
        errors="coerce",
    )

    periodos = (
        datas.dt.to_period("M")
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    return sorted(periodos, reverse=True)


def aplicar_filtros(
    df,
    banco="Todos",
    periodos=None,
    tipo="Todos",
    coluna_data=None,
    coluna_tipo=None,
):
    """Aplica os filtros selecionados nas movimentações."""

    df_filtrado = df.copy()

    if periodos and coluna_data and coluna_data in df_filtrado.columns:

        datas = pd.to_datetime(
            df_filtrado[coluna_data],
            errors="coerce",
        )

        df_filtrado = df_filtrado[
            datas.dt.strftime("%Y-%m").isin(periodos)
        ]

    if banco != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["banco_origem"] == banco
        ]

    if coluna_tipo and tipo != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado[coluna_tipo]
            .astype(str)
            .str.strip()
            .str.casefold()
            == tipo.casefold()
        ]

    return df_filtrado


# ============================================================
# VALORES MONETÁRIOS
# ============================================================

def converter_valor_monetario(valor):
    """Converte valores monetários brasileiros para números."""

    if valor is None or pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    valor = str(valor).strip()

    if not valor:
        return 0.0

    valor = (
        valor
        .replace("R$", "")
        .replace(" ", "")
    )

    negativo = valor.startswith("(") and valor.endswith(")")

    if negativo:
        valor = valor[1:-1]

    if "," in valor and "." in valor:

        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "").replace(",", ".")
        else:
            valor = valor.replace(",", "")

    elif "," in valor:
        valor = valor.replace(",", ".")

    resultado = float(valor)

    return -resultado if negativo else resultado


# ============================================================
# INDICADORES FINANCEIROS
# ============================================================

def calcular_indicadores(
    df,
    coluna_tipo,
    coluna_valor="Valor",
):
    """Calcula os indicadores financeiros das movimentações."""

    if df.empty:
        return {
            "total_movimentacoes": 0,
            "total_entradas": 0.0,
            "total_saidas": 0.0,
            "saldo": 0.0,
        }

    if coluna_valor not in df.columns:
        raise ValueError(
            f"A coluna '{coluna_valor}' não foi encontrada."
        )

    valores = df[coluna_valor].apply(
        converter_valor_monetario
    )

    # Caso não exista uma coluna de tipo,
    # identificar as entradas e saídas pelo sinal do valor.
    if not coluna_tipo or coluna_tipo not in df.columns:

        tipos = pd.Series(
            "não identificado",
            index=df.index,
        )

        tipos.loc[valores > 0] = "entrada"
        tipos.loc[valores < 0] = "saída"

    else:

        tipos = (
            df[coluna_tipo]
            .astype(str)
            .str.strip()
            .str.casefold()
        )

    entradas = valores[tipos == "entrada"].sum()

    saidas = valores[tipos == "saída"].abs().sum()

    saldo = entradas - saidas

    return {
        "total_movimentacoes": len(df),
        "total_entradas": entradas,
        "total_saidas": saidas,
        "saldo": saldo,
    }


def padronizar_movimentacoes(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    registros = []

    for _, linha in df.iterrows():

        # Identifica os campos de cada banco.
        data = obter_campo(
            linha,
            ["Data", "Date"],
        )

        valor_original = obter_campo(
            linha,
            ["Valor", "Amount", "BRL"],
        )

        descricao = obter_campo(
            linha,
            ["Descrição", "Descricao", "Description"],
        )

        detalhes = obter_campo(
            linha,
            ["Detalhes", "Details"],
        )

        lancamento = obter_campo(
            linha,
            ["Lançamento", "Lancamento", "Transaction"],
        )

        identificador = obter_campo(
            linha,
            ["Identificador", "ID", "Identifier"],
        )

        # Converte o valor para formato numérico.
        valor = converter_valor_monetario(valor_original)

        # Determina o tipo pelo sinal do valor.
        if valor is None:
            tipo = "Não identificado"

        elif valor > 0:
            tipo = "Entrada"

        elif valor < 0:
            tipo = "Saída"

        else:
            tipo = "Neutro"

        # Se o banco fornecer uma descrição única,
        # separa o lançamento dos detalhes.
        if descricao is not None and not pd.isna(descricao):

            partes = str(descricao).split(" - ", 1)

            lancamento = partes[0].strip()

            detalhes = (
                partes[1].strip()
                if len(partes) > 1
                else None
            )

            # Padroniza nomes conhecidos.
            nome_normalizado = normalizar_nome_coluna(lancamento)

            if nome_normalizado == "transferencia enviada pelo pix":
                lancamento = "Transferência Pix"

            elif nome_normalizado == "compra no debito":
                lancamento = "Compra no débito"

        registros.append({
            "Data": data,
            "Valor": valor,
            "Lançamento": lancamento,
            "Detalhes": detalhes,
            "Tipo": tipo,
            "Identificador": identificador,
        })

    return pd.DataFrame(registros)

