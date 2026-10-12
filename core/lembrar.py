import re

from core.memoria import carregar_memoria, salvar_memoria
from modules.util import normalizar_comando


def _responder_memoria(comando):
    consulta = normalizar_comando(comando)

    consultas = {
        "qual e meu time": ("time", "seu time"),
        "qual time eu torco": ("time", "seu time"),
        "qual e o nome do meu cachorro": ("cachorro", "o nome do seu cachorro"),
        "como chama meu cachorro": ("cachorro", "o nome do seu cachorro"),
    }
    perguntas_gerais = {
        "o que voce lembra", "o que voce lembra de mim", "o que voce sabe sobre mim",
        "quais informacoes voce guardou",
    }
    if consulta not in consultas and consulta not in perguntas_gerais:
        return None

    memoria = carregar_memoria()
    for frase, (chave, descricao) in consultas.items():
        if consulta == frase:
            valor = memoria.get(chave)
            if valor:
                return f"Lembro que {descricao} é {valor}."
            return f"Ainda não sei qual é {descricao}. Se me disser, posso guardar essa informação."

    if consulta in perguntas_gerais:
        fatos = memoria.get("fatos", [])
        if isinstance(fatos, str):
            fatos = [fatos]
        lembrancas = []
        if memoria.get("time"):
            lembrancas.append(f"seu time é {memoria['time']}")
        if memoria.get("cachorro"):
            lembrancas.append(f"seu cachorro se chama {memoria['cachorro']}")
        lembrancas.extend(fatos)
        if lembrancas:
            return "Lembro que " + "; ".join(lembrancas) + "."
        return "Ainda não guardei informações pessoais. Você pode dizer: lembre que..."

    return None


def _extrair_fato(comando):
    correspondencia = re.match(
        r"^(?:lembre|lembra|guarde|guarda|anote|anota)(?:-se)?\s+que\s+(.+?)\s*[.!?]*$",
        comando.strip(),
        flags=re.IGNORECASE,
    )
    if correspondencia:
        return correspondencia.group(1).strip()
    return None


def verificar(comando):
    resposta = _responder_memoria(comando)
    if resposta:
        return resposta

    comando_original = comando.strip()
    comando_normalizado = normalizar_comando(comando_original)

    for chave, prefixo, descricao in (
        ("time", "meu time e", "seu time"),
        ("cachorro", "meu cachorro chama", "o nome do seu cachorro"),
    ):
        if comando_normalizado.startswith(prefixo + " "):
            valor = comando_original[len(prefixo):].strip(" =.?!")
            if valor:
                salvar_memoria(chave, valor)
                return f"Entendido. Vou lembrar que {descricao} é {valor}."

    fato = _extrair_fato(comando_original)
    if not fato:
        return None

    memoria = carregar_memoria()
    fatos = memoria.get("fatos", [])
    if isinstance(fatos, str):
        fatos = [fatos]
    if normalizar_comando(fato) not in {normalizar_comando(item) for item in fatos}:
        fatos.append(fato)
        salvar_memoria("fatos", fatos)
    return f"Entendido. Vou lembrar que {fato}."
