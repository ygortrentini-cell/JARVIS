"""Pesquisa imagens e vídeos solicitados e abre os resultados no navegador."""

import re
import webbrowser
from urllib.parse import quote_plus

from .util import normalizar_comando


_TIPOS = r"imagens?|fotos?|videos?"
_PREPOSICAO = r"(?:de|do|da|dos|das|sobre|a respeito de)"


def _normalizar_tipo(tipo):
    return "vídeos" if tipo.startswith("video") else "imagens"


def extrair_pedido_visual(comando):
    """Retorna (tipo, busca, assunto_para_explicar) para pedidos visuais."""
    texto = normalizar_comando(comando)

    # Permite pedir uma explicação e, na mesma frase, imagens ou vídeos.
    composto = re.match(
        rf"^(?:por favor )?(?:(?:voce )?pode )?(?:me )?"
        rf"(?P<verbo>fale|fala|explique|explica|conte|conta)"
        rf"\s+(?:sobre|a respeito de)\s+(?P<assunto>.+?)\s+e\s+"
        rf"(?:me )?(?:mostre|mostra|exiba|exibir|coloque|abra)\s+"
        rf"(?:(?:um |uma |uns |umas |o |a |os |as ))?(?P<tipo>{_TIPOS})"
        rf"(?:\s+{_PREPOSICAO}\s+(?P<busca>.+))?$",
        texto,
    )
    if composto:
        assunto = composto.group("assunto").strip()
        busca = (composto.group("busca") or assunto).strip()
        tipo = _normalizar_tipo(composto.group("tipo"))
        return tipo, busca, assunto

    visual = re.match(
        rf"^(?:por favor )?(?:(?:voce )?pode )?(?:(?:eu )?quero )?"
        rf"(?:me )?(?:mostre|mostra|mostrar|exiba|exibir|procure|procura|"
        rf"pesquise|pesquisa|pesquisar|busque|busca|buscar|veja|ver|"
        rf"abra|abre|abrir|coloque)\s+"
        rf"(?:(?:um |uma |uns |umas |o |a |os |as ))?(?P<tipo>{_TIPOS})"
        rf"(?:\s+{_PREPOSICAO})?\s*(?P<busca>.*)$",
        texto,
    )
    if not visual:
        return None

    tipo = _normalizar_tipo(visual.group("tipo"))
    busca = visual.group("busca").strip()
    return tipo, busca, None


def abrir_pesquisa_visual(tipo, assunto):
    """Abre uma busca de imagens ou vídeos no navegador padrão."""
    consulta = quote_plus(assunto)
    if tipo == "vídeos":
        endereco = f"https://www.youtube.com/results?search_query={consulta}"
    else:
        endereco = f"https://www.google.com/search?tbm=isch&q={consulta}"

    try:
        return bool(webbrowser.open_new_tab(endereco))
    except Exception as erro:
        print(f"Não foi possível abrir a pesquisa visual: {erro}")
        return False
