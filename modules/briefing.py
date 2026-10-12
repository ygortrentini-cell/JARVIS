"""Resumo inicial com telemetria local e manchetes atuais."""

from datetime import datetime

from config import NOME_USUARIO
from modules.noticias import carregar_manchetes, formatar_manchetes
from modules.sistema import obter_resumo_sistema


def obter_briefing():
    """Monta um briefing curto sem consultar contas ou dados financeiros."""
    hora = datetime.now().hour
    if 5 <= hora < 12:
        saudacao = "Bom dia"
    elif 12 <= hora < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"

    telemetria = obter_resumo_sistema()
    manchetes = carregar_manchetes(limite=3)
    noticias = formatar_manchetes(manchetes)
    resposta = (
        f"{saudacao}, senhor {NOME_USUARIO}. Aqui está seu resumo de hoje.\n"
        f"Estado do computador: {telemetria}\n\n{noticias}"
    )
    return resposta, manchetes
