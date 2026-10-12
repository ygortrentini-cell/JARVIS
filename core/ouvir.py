"""Compatibilidade com scripts antigos que importavam `core.ouvir.ouvir`."""

from core.audio import Audio

_audio = None


def ouvir():
    global _audio
    if _audio is None:
        _audio = Audio()
    return _audio.ouvir()
