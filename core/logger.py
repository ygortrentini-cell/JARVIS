from datetime import datetime
from pathlib import Path

# Pasta de logs do projeto
PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_LOGS = PASTA_PROJETO / "logs"
PASTA_LOGS.mkdir(exist_ok=True)

ARQUIVO_LOG = PASTA_LOGS / "jarvis.log"


def log(texto):

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open(
        ARQUIVO_LOG,
        "a",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(f"[{agora}] {texto}\n")


def separador():

    with open(
        ARQUIVO_LOG,
        "a",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write("\n" + "=" * 70 + "\n\n")
