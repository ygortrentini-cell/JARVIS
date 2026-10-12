import webbrowser
from datetime import datetime
import re
import subprocess
import sys
from urllib.parse import quote_plus

from .programas import abrir_programa, fechar_programa
from .util import corrigir_transcricao, normalizar_comando


def separar_abertura_pesquisa(comando):
    comando = corrigir_transcricao(comando).lower().strip()
    correspondencia = re.match(
        r"^(?:abra|abre|abrir)\s+(?:(?:o|a)\s+)?(.+?)\s+e\s+"
        r"(?:pesquise|pesquisa|pesquisar|procure|procura|busque|busca)"
        r"(?:\s+(?:sobre|por))?(?:\s+(.+?))?[.!?]*$",
        comando,
    )
    if not correspondencia:
        return None

    programa = correspondencia.group(1).strip(" .!?")
    pesquisa = (correspondencia.group(2) or "").strip(" .!?")
    return (programa, pesquisa) if programa else None


def extrair_pesquisa_contextual(comando):
    comando = corrigir_transcricao(comando).lower().strip()
    correspondencia = re.match(
        r"^(?:dentro\s+(?:do|da|de)\s+|no\s+|na\s+)"
        r"(.+?)\s*,?\s+(?:pesquise|pesquisa|pesquisar|procure|procura|busque|busca)"
        r"(?:\s+(?:sobre|por))?(?:\s+(.+?))?[.!?]*$",
        comando,
    )
    if not correspondencia:
        return None

    navegador = correspondencia.group(1).strip(" ,.!?")
    pesquisa = (correspondencia.group(2) or "").strip(" .!?")
    return (navegador, pesquisa) if navegador else None


def extrair_pesquisa(comando):
    """Extrai pedidos de pesquisa, inclusive quando citam um navegador."""
    normalizado = normalizar_comando(comando)
    correspondencia = re.match(
        r"^(?:agora\s+)?(?:pesquise|pesquisa|pesquisar|procure|procura|buscar|busque|busca)\s+(.+)$",
        normalizado,
    )
    if not correspondencia:
        return None

    consulta = correspondencia.group(1).strip(" .!?")
    navegador = None
    sufixo = re.search(r"\s+no\s+(brave|chrome|edge|firefox)$", consulta)
    if sufixo:
        navegador = sufixo.group(1)
        consulta = consulta[:sufixo.start()].strip()
    consulta = re.sub(r"^(?:sobre|por)\s+", "", consulta).strip()
    return (navegador, consulta) if consulta else (navegador, "")


def executar_acao_windows(comando):
    """Executa comandos de sessão apenas para frases explícitas e inequívocas."""
    if sys.platform != "win32":
        return None

    if re.fullmatch(r"(?:por favor\s+)?cancelar desligamento", comando):
        acao = "cancelar"
    elif re.fullmatch(
        r"(?:por favor\s+)?(?:desligar|desligue|desliga)\s+(?:o\s+)?(?:computador|pc|windows)",
        comando,
    ):
        acao = "desligar"
    elif re.fullmatch(
        r"(?:por favor\s+)?(?:reiniciar|reinicie|reinicia)\s+(?:o\s+)?(?:computador|pc|windows)",
        comando,
    ):
        acao = "reiniciar"
    elif re.fullmatch(
        r"(?:por favor\s+)?(?:bloquear|bloqueie|bloqueia)\s+(?:o\s+)?(?:computador|pc|windows|sessao)",
        comando,
    ):
        acao = "bloquear"
    else:
        return None

    try:
        if acao == "bloquear":
            subprocess.Popen(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return "Bloqueando a sessão do Windows."

        argumentos = {
            "cancelar": ["shutdown.exe", "/a"],
            "desligar": ["shutdown.exe", "/s", "/t", "60"],
            "reiniciar": ["shutdown.exe", "/r", "/t", "60"],
        }[acao]
        resultado = subprocess.run(
            argumentos,
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return "Não consegui executar essa ação no Windows."

    if acao == "cancelar":
        return "Desligamento agendado cancelado." if resultado.returncode == 0 else "Não há desligamento agendado para cancelar."
    if resultado.returncode != 0:
        return "O Windows não aceitou o pedido de desligamento."
    return "O computador será desligado em 60 segundos. Para cancelar, diga “cancelar desligamento”." if acao == "desligar" else "O computador será reiniciado em 60 segundos."


def executar(comando):

    comando = corrigir_transcricao(comando).lower().strip()
    comando_normalizado = normalizar_comando(comando)

    resposta_sessao = executar_acao_windows(comando_normalizado)
    if resposta_sessao:
        return resposta_sessao

    # ===========================
    # DATA
    # ===========================

    consultas_data = (
        "que dia é hoje", "que dia e hoje", "qual é a data de hoje",
        "qual e a data de hoje", "qual a data de hoje", "data de hoje",
        "qual dia é hoje", "qual dia e hoje", "que dia", "qual é o dia",
        "qual e o dia", "qual a data", "que data é hoje", "que data e hoje",
    )
    if any(
        normalizar_comando(consulta) in comando_normalizado
        for consulta in consultas_data
    ):
        hoje = datetime.now()
        dias = (
            "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo",
        )
        meses = (
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        )
        return f"Hoje é {dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month - 1]} de {hoje.year}."

    # ===========================
    # PESQUISA EM NAVEGADOR ESPECÍFICO
    # ===========================

    pesquisa_contextual = extrair_pesquisa_contextual(comando)
    if pesquisa_contextual:
        navegador, pesquisa = pesquisa_contextual
        if not pesquisa:
            return f"O que devo pesquisar no {navegador}?"
        endereco = f"https://www.google.com/search?q={quote_plus(pesquisa)}"
        if abrir_programa(navegador, endereco=endereco):
            return f"Pesquisando {pesquisa} no {navegador}."
        return f"Não consegui abrir uma pesquisa no {navegador}."

    # ===========================
    # FECHAR PROGRAMAS
    # ===========================

    correspondencia_fechar = re.match(
        r"^(?:feche|fecha|fechar|encerre|encerrar|saia de|sair de)\s+(.+)$",
        comando_normalizado,
    )
    if correspondencia_fechar:
        nome = correspondencia_fechar.group(1).strip()
        nome = re.sub(r"^(?:o|a|os|as)\s+", "", nome)
        nome = re.sub(r"^(?:janela do|programa|aplicativo|app)\s+", "", nome)
        if nome in ("aba", "a aba", "guia", "a guia"):
            return "Para fechar uma aba, diga qual navegador está usando ou peça para fechar o navegador inteiro."
        if nome in ("navegador", "browser"):
            return "Qual navegador devo fechar: Brave, Chrome, Edge ou Firefox?"
        return fechar_programa(nome)

    # ===========================
    # HORAS
    # ===========================

    if any(frase in comando_normalizado for frase in ("que horas", "qual a hora", "me diga as horas")):

        agora = datetime.now()

        return f"Agora são {agora.hour} horas e {agora.minute} minutos."

    # ===========================
    # ABRIR PROGRAMAS
    # ===========================

    prefixo_abrir = next(
        (prefixo for prefixo in ("abra ", "abre ", "abrir ", "abra-me ") if comando.startswith(prefixo)),
        None,
    )
    if prefixo_abrir:

        nome = comando[len(prefixo_abrir):].strip().rstrip(" .!?")

        if nome.startswith("o "):
            nome = nome[2:]

        elif nome.startswith("a "):
            nome = nome[2:]

        return f"Abrindo {nome}." if abrir_programa(nome) else f"Não encontrei o programa {nome}."

    # ===========================
    # PESQUISAR NO GOOGLE
    # ===========================

    pesquisa = extrair_pesquisa(comando)
    if pesquisa:
        navegador, consulta = pesquisa
        if not consulta:
            return "O que devo pesquisar?"
        endereco = f"https://www.google.com/search?q={quote_plus(consulta)}"
        if navegador:
            if abrir_programa(navegador, endereco=endereco):
                return f"Pesquisando {consulta} no {navegador}."
            return f"Não consegui abrir uma pesquisa no {navegador}."
        webbrowser.open(endereco)
        return f"Pesquisando {consulta}."

    return None
