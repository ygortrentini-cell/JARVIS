import json
from pathlib import Path
from config import MAX_HISTORICO

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DADOS = PASTA_PROJETO / "dados"
ARQUIVO = PASTA_DADOS / "memoria.json"

PASTA_DADOS.mkdir(exist_ok=True)

memoria_conversa = []


def adicionar(role, mensagem):

    memoria_conversa.append({
        "role": role,
        "content": mensagem
    })

    if len(memoria_conversa) > MAX_HISTORICO:
        del memoria_conversa[:-MAX_HISTORICO]


def obter():
    return memoria_conversa


def carregar_memoria():

    if not ARQUIVO.exists():

        with ARQUIVO.open("w", encoding="utf-8") as f:
            json.dump({}, f)

    with ARQUIVO.open("r", encoding="utf-8") as f:
        return json.load(f)


def salvar_memoria(chave, valor):

    memoria = carregar_memoria()

    memoria[chave] = valor

    with ARQUIVO.open("w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)
