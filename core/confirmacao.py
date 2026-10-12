"""Autoriza ações do JARVIS conforme solicitado pelo usuário."""


class Confirmacao:
    """Compatibilidade com as ferramentas; não exibe diálogos de aprovação."""

    def pedir(self, titulo, resumo, detalhes="", tempo_limite=180):
        # O usuário configurou o JARVIS para agir sem confirmação prévia.
        return True
