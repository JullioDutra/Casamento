import unicodedata


def normalizar_nome(nome: str) -> str:
    """
    Remove acentos, caixa e espaços extras para comparar nomes de forma
    tolerante (ex: 'José da Silva ' e 'jose da silva' são considerados iguais).
    """
    nome = nome or ""
    nome = unicodedata.normalize("NFKD", nome).encode("ASCII", "ignore").decode("ASCII")
    return " ".join(nome.lower().split())
