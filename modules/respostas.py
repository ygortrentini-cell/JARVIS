import random
import re
from datetime import datetime
from .util import normalizar_comando
from config import NOME_USUARIO


SENHOR = f"senhor {NOME_USUARIO}" if NOME_USUARIO else "senhor"

RESPOSTAS = {

    "obrigado": [
        "Sempre às ordens.",
        "Foi um prazer ajudar.",
        f"Disponha, {SENHOR}."
    ],

    "valeu": [
        "Sempre às ordens.",
        "Disponha."
    ],

    "bom dia": [
        f"Bom dia, {SENHOR}.",
        "Bom dia. Estou pronto para ajudar."
    ],

    "boa tarde": [
        f"Boa tarde, {SENHOR}."
    ],

    "boa noite": [
        f"Boa noite, {SENHOR}."
    ],

    "como você está": [
        "Estou bem e funcionando normalmente. Obrigado por perguntar."
    ],

    "como voce esta": [
        "Estou bem e funcionando normalmente. Obrigado por perguntar."
    ],

    "como vai": [
        "Tudo certo por aqui. Como posso ajudar?"
    ],

    "e ai": [
        f"Tudo funcionando bem por aqui, {SENHOR}. O que precisa?",
        f"À disposição, {SENHOR}. Como posso ajudar?",
    ],

    "e ai se e": [
        f"À disposição, {SENHOR}. Como posso ajudar?"
    ],

    "como esta voce": [
        "Estou online e funcionando normalmente. Como posso ajudar?"
    ],

    "que dia bonito": [
        f"É verdade, {SENHOR}. Um dia bonito deixa tudo mais leve."
    ],

    "oi": [
        f"Olá, {SENHOR}.",
        "Olá. Como posso ajudar?"
    ],

    "olá": [
        f"Olá, {SENHOR}."
    ],

    "tudo bem": [
        "Tudo funcionando perfeitamente.",
        "Tudo certo por aqui."
    ],

    "quem é você": [
        "Sou Jarvis, seu assistente virtual."
    ],

    "o que voce pode fazer": [
        "Posso conversar, responder perguntas, pesquisar na web, abrir e fechar programas, consultar o sistema e ajudar com arquivos e código. Algumas ações dependem de uma solicitação clara.",
    ],

    "o que voce sabe fazer": [
        "Posso conversar, responder perguntas, pesquisar na web, abrir e fechar programas, consultar o sistema e ajudar com arquivos e código. Algumas ações dependem de uma solicitação clara.",
    ],

    "o que voce e capaz": [
        "Posso conversar, responder perguntas, pesquisar na web, abrir e fechar programas, consultar o sistema e ajudar com arquivos e código. Algumas ações dependem de uma solicitação clara.",
    ]
}


def resposta_rapida(comando):

    comando = normalizar_comando(comando)

    perguntas_data = {
        "que dia e hoje", "qual e a data de hoje", "qual a data de hoje",
        "que data e hoje", "me diga a data de hoje",
    }
    if comando in perguntas_data:
        agora = datetime.now()
        dias = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                "sexta-feira", "sábado", "domingo")
        meses = ("janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
        return (
            f"Hoje é {dias[agora.weekday()]}, {agora.day} de "
            f"{meses[agora.month - 1]} de {agora.year}."
        )

    for chave in RESPOSTAS:

        chave_normalizada = normalizar_comando(chave)
        if re.search(rf"\b{re.escape(chave_normalizada)}\b", comando):

            return random.choice(RESPOSTAS[chave])

    return None
