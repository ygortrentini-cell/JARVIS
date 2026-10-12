"""Pesquisa imagens e vídeos solicitados e abre os resultados no navegador."""

import os
import re
import time
import webbrowser
from threading import Thread
from urllib.parse import quote_plus

from .util import normalizar_comando


_TIPOS = r"imagens?|fotos?|videos?"
_PREPOSICAO = r"(?:de|do|da|dos|das|sobre|a respeito de)"
URI_SPOTIFY_BACK_IN_BLACK = "spotify:track:08mG3Y1vljYA6bvDt4Wqkj"


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


def tocar_back_in_black():
    """Aciona a faixa no Spotify e tenta manter a janela do player oculta."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        shell32.ShellExecuteW.argtypes = (
            wintypes.HWND,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            ctypes.c_int,
        )
        shell32.ShellExecuteW.restype = ctypes.c_void_p
        # SW_HIDE evita pedir ao Windows que mostre a janela do aplicativo.
        resultado = shell32.ShellExecuteW(
            None, "open", URI_SPOTIFY_BACK_IN_BLACK, None, None, 0
        )
        if not resultado or resultado <= 32:
            return False
    except Exception:
        return False

    Thread(
        target=_ocultar_janelas_spotify,
        name="jarvis-ocultar-spotify",
        daemon=True,
    ).start()
    return True


def _ocultar_janelas_spotify():
    """Oculta a janela do Spotify para deixar visível somente o JARVIS."""
    try:
        import ctypes
        import psutil
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.IsWindowVisible.argtypes = (wintypes.HWND,)
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
        user32.ShowWindow.restype = wintypes.BOOL
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )
        user32.EnumWindows.argtypes = (callback_type, wintypes.LPARAM)
        user32.EnumWindows.restype = wintypes.BOOL

        limite = time.monotonic() + 10
        while time.monotonic() < limite:
            encontrou = False

            def minimizar(hwnd, _parametro):
                nonlocal encontrou
                if not user32.IsWindowVisible(hwnd):
                    return True
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    nome = psutil.Process(pid.value).name().casefold()
                except (psutil.Error, OSError):
                    return True
                if nome == "spotify.exe":
                    user32.ShowWindow(hwnd, 0)  # SW_HIDE
                    encontrou = True
                return True

            callback = callback_type(minimizar)
            user32.EnumWindows(callback, 0)
            if encontrou:
                return
            time.sleep(0.02)
    except Exception:
        return
