"""Leitura de notícias recentes da Agência Brasil por RSS."""

import html
import re
import time
from threading import Lock
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from config import NOME_USUARIO


FEED_NOTICIAS = "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml"
FEEDS_DESCOBERTAS = (
    (
        "Pesquisa e Inovação · Radioagência Nacional",
        "https://agenciabrasil.ebc.com.br/radioagencia-nacional/rss/pesquisa-e-inovacao/feed.xml",
    ),
    ("NASA JPL", "https://www.jpl.nasa.gov/feeds/news/"),
)
_CACHE_TTL = 120
_CACHE = []
_CACHE_ATUALIZADO = 0.0
_CACHE_DESCOBERTAS = []
_CACHE_DESCOBERTAS_ATUALIZADO = 0.0
_CACHE_NOTICIAS_LOCK = Lock()
_CACHE_DESCOBERTAS_LOCK = Lock()


def _texto(elemento):
    if elemento is None:
        return ""
    texto = "".join(elemento.itertext())
    texto = html.unescape(texto)
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _valor(item, *nomes):
    for elemento in item.iter():
        nome = elemento.tag.rsplit("}", 1)[-1].lower()
        if nome in nomes:
            texto = _texto(elemento)
            if texto:
                return texto
    return ""


def _imagem(item):
    for elemento in item.iter():
        trecho = "".join(elemento.itertext())
        embutida = re.search(
            r"<img\b[^>]*\b(?:src|data-src)\s*=\s*['\"]([^'\"]+)['\"]",
            trecho,
            flags=re.IGNORECASE,
        )
        if embutida:
            endereco = html.unescape(embutida.group(1)).strip()
            if endereco.startswith(("https://", "http://")):
                return endereco

        nome = elemento.tag.rsplit("}", 1)[-1].lower()
        if nome in {"thumbnail", "content", "enclosure"}:
            endereco = elemento.attrib.get("url", "").strip()
            tipo = elemento.attrib.get("type", "").lower()
            if endereco.startswith(("https://", "http://")) and (
                nome != "enclosure" or not tipo or tipo.startswith("image/")
            ):
                return endereco
    return ""


def _artigo(item, fonte_padrao="Agência Brasil", categoria_padrao="Destaque"):
    titulo = _valor(item, "title")
    if not titulo:
        return None

    link = _valor(item, "link")
    if not link:
        link = next(
            (
                elemento.attrib.get("href", "").strip()
                for elemento in item.iter()
                if elemento.tag.rsplit("}", 1)[-1].lower() == "link"
                and elemento.attrib.get("href", "").strip()
            ),
            "",
        )

    resumo = _valor(item, "description", "summary", "encoded")
    categoria = _valor(item, "category") or categoria_padrao
    fonte = _valor(item, "source") or fonte_padrao
    publicado = _valor(item, "pubdate", "published", "updated")
    return {
        "titulo": titulo,
        "resumo": resumo,
        "categoria": categoria,
        "fonte": fonte,
        "publicado": publicado,
        "link": link,
        "imagem": _imagem(item),
    }


def _ler_feed(url, limite, fonte_padrao):
    requisicao = urllib.request.Request(
        url,
        headers={"User-Agent": "JarvisAssistente/1.0 (leitor RSS)"},
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=4) as resposta:
            conteudo = resposta.read(1_000_000)
        raiz = ET.fromstring(conteudo)
    except (OSError, urllib.error.URLError, ET.ParseError, TimeoutError):
        return None

    itens = raiz.findall(".//item")
    if not itens:
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        itens = raiz.findall(".//atom:entry", namespace)

    artigos = []
    vistos = set()
    for item in itens:
        artigo = _artigo(item, fonte_padrao, fonte_padrao)
        if not artigo or artigo["titulo"] in vistos:
            continue
        vistos.add(artigo["titulo"])
        artigo["fonte"] = artigo.get("fonte") or fonte_padrao
        artigo["categoria"] = artigo.get("categoria") or fonte_padrao
        artigos.append(artigo)
        if len(artigos) >= limite:
            break
    return artigos


def carregar_manchetes(limite=3):
    """Busca as matérias mais recentes; retorna None quando o feed falha."""
    global _CACHE, _CACHE_ATUALIZADO
    limite = max(1, min(int(limite), 5))

    with _CACHE_NOTICIAS_LOCK:
        agora = time.monotonic()
        if _CACHE and agora - _CACHE_ATUALIZADO < _CACHE_TTL:
            return [dict(item) for item in _CACHE[:limite]]

        artigos = _ler_feed(FEED_NOTICIAS, 5, "Agência Brasil")
        if artigos is None:
            return None
        _CACHE = artigos
        _CACHE_ATUALIZADO = time.monotonic()
        return [dict(item) for item in artigos[:limite]]


def carregar_descobertas(limite=3):
    """Reúne novidades científicas e tecnológicas de feeds públicos confiáveis."""
    global _CACHE_DESCOBERTAS, _CACHE_DESCOBERTAS_ATUALIZADO
    limite = max(1, min(int(limite), 5))

    with _CACHE_DESCOBERTAS_LOCK:
        agora = time.monotonic()
        if _CACHE_DESCOBERTAS and agora - _CACHE_DESCOBERTAS_ATUALIZADO < 900:
            return [dict(item) for item in _CACHE_DESCOBERTAS[:limite]]

        lotes = []
        falhas = 0
        for fonte, url in FEEDS_DESCOBERTAS:
            resultados = _ler_feed(url, limite, fonte)
            if resultados is None:
                falhas += 1
                continue
            for artigo in resultados:
                artigo["tipo"] = "descoberta"
            lotes.append(resultados)
        if falhas == len(FEEDS_DESCOBERTAS):
            return None

        vistos = set()
        unicos = []
        for indice in range(max((len(lote) for lote in lotes), default=0)):
            for lote in lotes:
                if indice >= len(lote):
                    continue
                artigo = lote[indice]
                chave = artigo["titulo"].casefold()
                if chave not in vistos:
                    vistos.add(chave)
                    unicos.append(artigo)
        _CACHE_DESCOBERTAS = unicos
        _CACHE_DESCOBERTAS_ATUALIZADO = time.monotonic()
        return [dict(item) for item in unicos[:limite]]


def formatar_manchetes(manchetes):
    """Converte matérias do feed em uma resposta curta e falada."""
    if manchetes is None:
        return (
            "Não consegui acessar as notícias agora. Tente novamente em instantes "
            "ou peça para pesquisar um assunto no navegador."
        )
    if not manchetes:
        return "A Agência Brasil não retornou manchetes neste momento."

    titulos = [
        item.get("titulo", "") if isinstance(item, dict) else str(item)
        for item in manchetes
    ]
    lista = " ".join(f"{titulo.rstrip('.!?')}." for titulo in titulos if titulo)
    return f"Estas são as últimas manchetes da Agência Brasil, senhor {NOME_USUARIO}. {lista} Fonte: Agência Brasil."


def obter_noticias(limite=3):
    """Retorna manchetes recentes; falhas de rede viram uma resposta amigável."""
    return formatar_manchetes(carregar_manchetes(limite))
