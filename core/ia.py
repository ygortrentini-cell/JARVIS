"""Compatibilidade com a API antiga de perguntas à IA."""

from core.inteligencia import Inteligencia

_inteligencia = None


def perguntar_ia(pergunta):
    global _inteligencia
    if _inteligencia is None:
        _inteligencia = Inteligencia()
    return _inteligencia.perguntar(pergunta)
