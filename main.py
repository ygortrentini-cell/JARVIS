"""Ponto único de entrada do J.A.R.V.I.S."""

import sys

from core.assistente import Assistente


def _preparar_console():
    """Evita que o console cp1252 interrompa a inicialização por emojis/símbolos."""
    for fluxo in (sys.stdout, sys.stderr):
        if fluxo is not None and hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(errors="replace")


def main():
    _preparar_console()
    assistente = Assistente()
    assistente.iniciar()


if __name__ == "__main__":
    main()
