"""Consulta o resumo local da última versão instalada do JARVIS."""

import json
from pathlib import Path
import time

from modules.util import normalizar_comando


ARQUIVO_ATUALIZACAO = Path(__file__).resolve().parents[1] / "dados" / "ultima_atualizacao.json"
ARQUIVO_CONHECIMENTO = Path(__file__).resolve().parents[1] / "dados" / "conhecimento_recente.json"
PEDIDOS_APRENDIZADO = {
    "o que voce aprendeu",
    "o que voce aprendeu recentemente",
    "o que voce aprendeu na ultima atualizacao",
    "o que mudou na ultima atualizacao",
    "quais as novidades do jarvis",
    "como voce se melhorou",
    "o que voce aprendeu da ultima vez",
    "o que voce aprendeu na ultima versao",
    "o que voce aprendeu nessa atualizacao",
    "o que voce aprendeu com a atualizacao",
    "o que mudou no jarvis",
}


def registrar_descobertas(descobertas):
    if not isinstance(descobertas, list) or not descobertas:
        return

    try:
        existentes = json.loads(ARQUIVO_CONHECIMENTO.read_text(encoding="utf-8"))
        if not isinstance(existentes, list):
            existentes = []
    except (OSError, ValueError, TypeError):
        existentes = []

    por_chave = {}
    for artigo in [*existentes, *descobertas]:
        if not isinstance(artigo, dict):
            continue
        titulo = str(artigo.get("titulo", "")).strip()[:180]
        fonte = str(artigo.get("fonte", "Pesquisa")).strip()[:80]
        if not titulo:
            continue
        resumo = str(artigo.get("resumo", "")).strip()[:240]
        link = str(artigo.get("link", "")).strip()[:500]
        chave = link or f"{fonte}|{titulo}".casefold()
        anterior = por_chave.get(chave, {})
        por_chave[chave] = {
            "titulo": titulo,
            "fonte": fonte,
            "resumo": resumo,
            "link": link,
            "registrado_em": artigo.get("registrado_em") or anterior.get("registrado_em") or time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    arquivo_temporario = ARQUIVO_CONHECIMENTO.with_suffix(".json.tmp")
    try:
        ARQUIVO_CONHECIMENTO.parent.mkdir(parents=True, exist_ok=True)
        arquivo_temporario.write_text(
            json.dumps(list(por_chave.values())[-60:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        arquivo_temporario.replace(ARQUIVO_CONHECIMENTO)
    except OSError:
        return


def responder_aprendizado(comando):
    comando_normalizado = normalizar_comando(comando)
    if comando_normalizado not in PEDIDOS_APRENDIZADO:
        return None

    partes = []
    try:
        dados = json.loads(ARQUIVO_ATUALIZACAO.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        dados = None

    if isinstance(dados, dict):
        versao = str(dados.get("versao", "recente"))
        mudancas = str(dados.get("mudancas", "Melhorias e correções."))
        aprendizados = str(dados.get("aprendizados", "Nenhum aprendizado novo foi especificado."))
        partes.append(
            f"Na versão {versao}, mudou: {mudancas} Conhecimento registrado: {aprendizados}"
        )

    try:
        descobertas = json.loads(ARQUIVO_CONHECIMENTO.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        descobertas = []
    if isinstance(descobertas, list) and descobertas:
        destaques = [
            f"{item.get('fonte', 'Pesquisa')}: {item.get('titulo', '')}"
            for item in descobertas[-2:]
            if isinstance(item, dict) and item.get("titulo")
        ]
        if destaques:
            partes.append("Também acompanhei estas descobertas recentes: " + "; ".join(destaques))

    if not partes:
        return "Ainda não tenho uma atualização ou descoberta registrada. Quando encontrar novidades nos feeds, vou guardá-las para você."
    return " ".join(partes)
