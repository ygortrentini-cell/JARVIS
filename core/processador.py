from core.memoria import adicionar
from core.lembrar import verificar
import re
from modules.arquivos import executar_arquivo
from modules.calculadora import calcular
from modules.comandos import (
    executar as executar_comando,
    separar_abertura_pesquisa,
)
from modules.respostas import resposta_rapida
from modules.sistema import executar_sistema
from modules.util import corrigir_transcricao, normalizar_comando
from modules.noticias import carregar_manchetes, formatar_manchetes
from modules.midia import abrir_pesquisa_visual, extrair_pedido_visual
from modules.briefing import obter_briefing
from modules.aprendizado import responder_aprendizado


class Processador:
    """Encaminha pedidos para ações locais rápidas ou para o modelo de IA."""

    def __init__(self, inteligencia):
        self.inteligencia = inteligencia
        self._acao_pendente = None
        self.ultimas_manchetes = None
        self.atualizou_manchetes = False
        self.verificar_atualizacao_callback = None

    @staticmethod
    def _acao_arquivo(comando):
        comando = comando.lower()
        verbo = comando.startswith(
            ("abra ", "abre ", "abrir ", "acesse ", "acessar ", "mostre ", "mostrar ")
        )
        pasta_conhecida = any(
            termo in comando
            for termo in ("downloads", "documentos", "área de trabalho", "desktop")
        )
        return verbo and pasta_conhecida

    @staticmethod
    def _criacao_arquivo_ou_pasta(comando):
        comando = comando.lower()
        return any(
            termo in comando
            for termo in ("crie uma pasta chamada", "crie um arquivo chamado")
        )

    @staticmethod
    def _pede_briefing(comando_normalizado):
        saudacoes = {
            "bom dia", "bom dia jarvis", "boa tarde", "boa tarde jarvis",
            "boa noite", "boa noite jarvis",
        }
        pedidos = {
            "briefing", "resumo do dia", "resumo de hoje", "resumo da manha",
            "o que importa hoje", "o que e importante hoje",
            "o que preciso saber hoje", "me atualize",
        }
        return comando_normalizado in saudacoes or comando_normalizado in pedidos

    @staticmethod
    def _registrar_resposta_local(comando, resposta):
        adicionar("user", comando)
        adicionar("assistant", resposta)
        return resposta

    def perguntar(self, texto, origem_voz=False):
        self.ultimas_manchetes = None
        self.atualizou_manchetes = False
        comando = corrigir_transcricao(texto.strip())
        if not comando:
            return ""

        comando_normalizado = normalizar_comando(comando)

        pedidos_atualizacao = {
            "verifique atualizacoes", "verificar atualizacoes",
            "cheque atualizacoes", "checar atualizacoes",
            "busque atualizacoes", "buscar atualizacoes",
            "procure atualizacoes", "procurar atualizacoes",
            "atualize jarvis", "atualize o jarvis", "atualiza jarvis",
            "atualize o sistema do jarvis", "atualize se jarvis",
            "atualizar jarvis agora", "verificar atualizacao",
            "checar atualizacao", "buscar atualizacao", "procurar atualizacao",
        }
        verbo_atualizacao = any(
            verbo in comando_normalizado.split()
            for verbo in ("verificar", "verifique", "checar", "cheque", "buscar", "busque", "procurar", "procure")
        )
        menciona_atualizacao = any(
            termo in comando_normalizado.split()
            for termo in ("atualizacao", "atualizacoes")
        )
        if comando_normalizado in pedidos_atualizacao or (verbo_atualizacao and menciona_atualizacao):
            if self.verificar_atualizacao_callback:
                self.verificar_atualizacao_callback()
            return self._registrar_resposta_local(
                comando,
                "Vou verificar se há uma versão nova. Se encontrar, aviso e preparo a atualização para o próximo encerramento.",
            )

        resposta = responder_aprendizado(comando_normalizado)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        if self._pede_briefing(comando_normalizado):
            resposta, self.ultimas_manchetes = obter_briefing()
            self.atualizou_manchetes = True
            return self._registrar_resposta_local(comando, resposta)

        pedido_visual = extrair_pedido_visual(comando)
        if pedido_visual:
            tipo, consulta, assunto_para_explicar = pedido_visual
            if not consulta:
                resposta = f"Sobre qual assunto devo pesquisar {tipo}?"
                return self._registrar_resposta_local(comando, resposta)

            abriu = abrir_pesquisa_visual(tipo, consulta)
            if tipo == "vídeos":
                resposta_visual = f"Abri vídeos sobre {consulta} no YouTube." if abriu else "Não consegui abrir a busca de vídeos."
            else:
                resposta_visual = f"Abri imagens de {consulta} no navegador." if abriu else "Não consegui abrir a busca de imagens."

            if assunto_para_explicar:
                explicacao = self.inteligencia.perguntar(
                    f"Explique {assunto_para_explicar}", origem_voz=origem_voz
                )
                resposta = f"{explicacao}\n\n{resposta_visual}" if explicacao else resposta_visual
            else:
                resposta = resposta_visual
            return self._registrar_resposta_local(comando, resposta)

        afirmacoes = {
            "claro", "sim", "pode", "pode consultar", "pode verificar",
            "com certeza", "isso", "claro que sim", "pode sim", "por favor",
        }
        negativas = {"nao", "nao precisa", "deixa", "deixe", "cancela", "cancelar", "agora nao"}
        if self._acao_pendente == "consultar_sistema":
            self._acao_pendente = None
            if comando_normalizado in afirmacoes:
                resposta = executar_sistema("consultar sistema")
                if resposta:
                    return self._registrar_resposta_local(comando, resposta)
            if comando_normalizado in negativas:
                return self._registrar_resposta_local(comando, "Tudo bem. Não vou consultar o sistema.")

        resposta = resposta_rapida(comando)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        resposta = calcular(comando)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        resposta = executar_sistema(comando)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        resposta = verificar(comando)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        # Manchetes precisam de informação atual; não delegue esse pedido ao
        # modelo local, que pode não ter acesso à internet nem dados recentes.
        if any(termo in comando_normalizado.split() for termo in ("noticia", "noticias", "manchete", "manchetes")):
            assunto = re.search(
                r"\b(?:noticias?|manchetes?)\s+(?:sobre|de|do|da|dos|das)\s+(.+)$",
                comando_normalizado,
            )
            if assunto and assunto.group(1).strip() not in {
                "hoje", "agora", "dia", "ultimas", "recentes", "do dia",
            }:
                resposta = executar_comando(f"pesquise notícias sobre {assunto.group(1)}")
                if resposta:
                    return self._registrar_resposta_local(comando, resposta)
            self.ultimas_manchetes = carregar_manchetes(limite=3)
            self.atualizou_manchetes = True
            resposta = formatar_manchetes(self.ultimas_manchetes)
            return self._registrar_resposta_local(comando, resposta)

        if self._acao_arquivo(comando) and not self._criacao_arquivo_ou_pasta(comando):
            resposta = executar_arquivo(comando)
            if resposta:
                return self._registrar_resposta_local(comando, resposta)

        # Criações e outros pedidos de arquivo são tratados pela ferramenta da IA.

        plano_composto = separar_abertura_pesquisa(comando)
        if plano_composto:
            programa, pesquisa = plano_composto
            navegadores = {"brave", "chrome", "edge", "firefox", "navegador", "browser"}
            if programa in navegadores and pesquisa:
                resposta = executar_comando(f"dentro do {programa} pesquise sobre {pesquisa}")
                return self._registrar_resposta_local(comando, resposta or "Não consegui abrir a pesquisa.")

            resposta_abertura = executar_comando(f"abra {programa}")
            if not resposta_abertura or resposta_abertura.startswith("Não encontrei"):
                return self._registrar_resposta_local(comando, resposta_abertura or "Não consegui abrir o programa.")
            if not pesquisa:
                return self._registrar_resposta_local(comando, f"{resposta_abertura} O que devo pesquisar?")
            resposta_pesquisa = executar_comando(f"pesquise sobre {pesquisa}")
            return self._registrar_resposta_local(comando, f"{resposta_abertura} {resposta_pesquisa or ''}".strip())

        resposta = executar_comando(comando)
        if resposta:
            return self._registrar_resposta_local(comando, resposta)

        resposta = self.inteligencia.perguntar(comando, origem_voz=origem_voz)
        resposta_normalizada = normalizar_comando(resposta or "")
        ofereceu_consulta = (
            "sistema" in resposta_normalizada
            or any(
                termo in resposta_normalizada
                for termo in ("cpu", "memoria", "bateria", "disco")
            )
        ) and any(
            frase in resposta_normalizada
            for frase in (
                "posso consultar", "posso verificar", "quer que eu consulte",
                "quer que eu verifique",
            )
        )
        self._acao_pendente = "consultar_sistema" if ofereceu_consulta else None
        return resposta
