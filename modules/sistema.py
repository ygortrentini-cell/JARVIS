import socket
import os
from pathlib import Path
from modules.util import normalizar_comando

try:
    import psutil
except ImportError:
    psutil = None


def _numero_pt(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def obter_resumo_sistema():
    """Retorna um resumo local e curto da telemetria do computador."""
    if psutil is None:
        return "A telemetria do computador não está disponível."

    try:
        uso_cpu = psutil.cpu_percent(interval=0.2)
        memoria = psutil.virtual_memory()
        ram_usada = memoria.used / (1024**3)
        ram_total = memoria.total / (1024**3)
        unidade_sistema = Path.home().anchor or "C:\\"
        disco = psutil.disk_usage(unidade_sistema)
        disco_livre = disco.free / (1024**3)
        disco_total = disco.total / (1024**3)

        resumo = (
            f"CPU em {_numero_pt(uso_cpu, 0)}%; RAM em "
            f"{_numero_pt(ram_usada)} de {_numero_pt(ram_total)} GB; "
            f"armazenamento com {_numero_pt(disco_livre)} GB livres "
            f"de {_numero_pt(disco_total)} GB."
        )

        bateria = psutil.sensors_battery()
        if bateria is not None:
            estado = " e carregando" if bateria.power_plugged else ""
            resumo += f" Bateria em {bateria.percent}%{estado}."
        return resumo
    except (OSError, ValueError, AttributeError, NotImplementedError):
        return "Não consegui consultar a telemetria do computador agora."


def executar_sistema(comando):

    comando = normalizar_comando(comando)
    palavras = set(comando.split())

    # Aceita formas naturais comuns, inclusive variações que o Whisper costuma
    # produzir quando o usuário pede para mostrar ou verificar o sistema.
    verbos_consulta = {
        "como esta", "como estao", "verificar", "verifique", "consultar",
        "consulte", "status", "estado", "checar", "cheque", "mostrar",
        "mostra", "mostre", "mostro", "exibir", "exiba", "ver", "veja",
        "mostrar-me", "me mostre", "me mostra", "me diga", "diga",
    }

    consulta_geral = (
        bool(palavras.intersection({"sistema", "sistemas"}))
        and any(
            normalizar_comando(verbo) in comando
            for verbo in verbos_consulta
        )
    )

    if psutil is None and any(
        termo in comando
        for termo in ("cpu", "processador", "ram", "memoria", "bateria", "disco", "sistema")
    ):
        return "O monitoramento do sistema não está disponível. Instale as dependências do projeto."

    if consulta_geral:
        return "Estado do computador: " + obter_resumo_sistema()

    # ===========================
    # CPU
    # ===========================

    if "cpu" in comando or "processador" in comando:

        uso = psutil.cpu_percent(interval=0.2)

        return f"O processador está utilizando {uso} por cento."

    # ===========================
    # MEMÓRIA RAM
    # ===========================

    if "ram" in comando or "memoria" in comando:

        memoria = psutil.virtual_memory()

        total = round(memoria.total / (1024**3), 1)
        usada = round(memoria.used / (1024**3), 1)

        return (
            f"Você está utilizando {usada} GB de "
            f"{total} GB de memória RAM."
        )

    # ===========================
    # BATERIA
    # ===========================

    if "bateria" in comando:

        bateria = psutil.sensors_battery()

        if bateria is None:
            return "Este computador não possui bateria."

        if bateria.power_plugged:
            return f"A bateria está em {bateria.percent}% e carregando."

        return f"A bateria está em {bateria.percent}%."

    # ===========================
    # DISCO
    # ===========================

    if "disco" in comando:

        disco = psutil.disk_usage("C:\\")

        livre = round(disco.free / (1024**3), 1)

        total = round(disco.total / (1024**3), 1)

        return f"Você possui {livre} GB livres de {total} GB."

    # ===========================
    # IP
    # ===========================

    if "ip" in comando:

        ip = socket.gethostbyname(socket.gethostname())

        return f"Seu IP é {ip}."

    # ===========================
    # NOME DO COMPUTADOR
    # ===========================

    if "nome do computador" in comando:

        return f"O nome deste computador é {socket.gethostname()}."

    # ===========================
    # USUÁRIO
    # ===========================

    if "meu usuario" in comando:

        return f"O usuário atual é {os.getlogin()}."

    return None
