import json
import sys
import os
from datetime import datetime
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QObject, QSettings, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from config import NOME_USUARIO
from core.audio import Audio
from core.voz import Voz
from core.inteligencia import Inteligencia
from core.processador import Processador
from core.logger import log
from core.confirmacao import Confirmacao
from modules.sistema import obter_resumo_sistema
from modules.noticias import carregar_descobertas, carregar_manchetes
from modules.aprendizado import registrar_descobertas
from modules.atualizador import Atualizador
from modules.midia import tocar_back_in_black

from core.worker_audio import WorkerAudio
from core.worker_ia import WorkerIA
from core.worker_voz import WorkerVoz

from interface.janela import JanelaJarvis


class Assistente(QObject):
    comando_manual = Signal(str)
    fala_solicitada = Signal(str)
    manchetes_iniciais = Signal(object)
    descobertas_iniciais = Signal(object, object)
    atualizacao_inicial = Signal(object)

    def __init__(self):

        super().__init__()

        print("=" * 45)
        print("          J.A.R.V.I.S.")
        print("=" * 45)

        # -------------------------
        # APLICAÇÃO
        # -------------------------

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("J.A.R.V.I.S.")
        self.aviso_atualizacao = self._ler_atualizacao_pendente()
        self._anunciar_atualizacao_na_abertura = self.aviso_atualizacao is not None

        self.janela = JanelaJarvis()
        self.confirmacao = Confirmacao()
        self.atualizador = Atualizador()
        self.janela.showMaximized()
        self.app.processEvents()
        self.mensagem_abertura = self._mensagem_abertura(self.aviso_atualizacao)

        # -------------------------
        # MÓDULOS
        # -------------------------

        print("\nCarregando módulos...")

        self.audio = Audio()
        self.ia = Inteligencia(self.confirmacao)
        self.processador = Processador(self.ia)
        self.processador.verificar_atualizacao_callback = self._solicitar_verificacao_atualizacao
        self.voz = Voz()

        if not self.audio.disponivel:
            self.janela.marcar_microfone_indisponivel(self.audio.erro)

        # -------------------------
        # WORKER DO ÁUDIO
        # -------------------------

        self.worker_audio = WorkerAudio(self.audio)

        # -------------------------
        # THREAD + WORKER DA IA
        # -------------------------

        self.thread_ia = QThread()
        self.worker_ia = WorkerIA(self.processador)

        self.worker_ia.moveToThread(self.thread_ia)

        # -------------------------
        # THREAD + WORKER DA VOZ
        # -------------------------

        self.thread_voz = QThread()
        self.worker_voz = WorkerVoz(self.voz)

        self.worker_voz.moveToThread(self.thread_voz)
        self.fala_solicitada.connect(self.worker_voz.falar)

        # -------------------------
        # ÁUDIO → ASSISTENTE
        # -------------------------

        self.worker_audio.comando.connect(
            self.receber_comando
        )
        self.worker_audio.gesto_palmas.connect(self._ao_detectar_duas_palmas)

        # -------------------------
        # ASSISTENTE → IA
        # -------------------------

        self.worker_audio.comando.connect(
            self.worker_ia.processar_voz
        )

        # -------------------------
        # IA → ASSISTENTE
        # -------------------------

        self.worker_ia.resposta.connect(
            self.receber_resposta
        )
        self.worker_ia.manchetes.connect(self.janela.atualizar_manchetes)
        self.manchetes_iniciais.connect(self.janela.atualizar_manchetes)
        self.descobertas_iniciais.connect(self.janela.atualizar_descobertas)
        self.atualizacao_inicial.connect(self._receber_resultado_atualizacao)
        self.janela.enviar_comando.connect(self.receber_texto)
        self.comando_manual.connect(self.worker_ia.processar)

        self.janela.alternar_microfone.connect(
            self.worker_audio.definir_escuta
        )

        # -------------------------
        # IA → VOZ
        # -------------------------

        self.worker_ia.resposta.connect(
            self.worker_voz.falar
        )

        # -------------------------
        # ESTADOS DA INTERFACE
        # -------------------------

        self.worker_audio.ouvindo.connect(
            self.janela.estado_ouvindo
        )

        self.worker_ia.pensando.connect(
            self.janela.estado_pensando
        )

        self.worker_voz.falando.connect(
            self.janela.estado_falando
        )

        # -------------------------
        # ERROS
        # -------------------------

        self.worker_audio.erro.connect(self._erro_audio)
        self.worker_ia.erro.connect(self._erro_ia)
        self.worker_voz.erro.connect(self._erro_voz)

        # -------------------------
        # FIM DA FALA
        # -------------------------

        self.worker_voz.terminou.connect(
            self.fala_terminou
        )

        # -------------------------
        # ENCERRAMENTO
        # -------------------------

        self.app.aboutToQuit.connect(
            self.encerrar
        )

        self.janela.adicionar_mensagem(
            "JARVIS",
            self.mensagem_abertura,
        )
        self._solicitar_atualizacao_manchetes()
        self.timer_manchetes = QTimer(self)
        self.timer_manchetes.setInterval(30 * 60 * 1000)
        self.timer_manchetes.timeout.connect(self._solicitar_atualizacao_manchetes)
        self.timer_manchetes.start()
        self._solicitar_verificacao_atualizacao()
        self.timer_atualizacao = QTimer(self)
        self.timer_atualizacao.setInterval(60 * 60 * 1000)
        self.timer_atualizacao.timeout.connect(self._solicitar_verificacao_atualizacao)
        self.timer_atualizacao.start()
        log("J.A.R.V.I.S. iniciado.")

        print("\n✓ J.A.R.V.I.S. carregado.")
        print("✓ Interface pronta.")
        print("✓ Áudio pronto." if self.audio.disponivel else "• Áudio indisponível; entrada por texto disponível.")
        print("✓ Inteligência pronta.")
        print("✓ Voz pronta.")

    @staticmethod
    def _ler_atualizacao_pendente():
        raiz = Path(__file__).resolve().parents[1]
        arquivo = raiz / "dados" / "ultima_atualizacao.json"
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            dados = None
        if isinstance(dados, dict) and not dados.get("anunciada"):
            return dados

        # Compatibilidade com a v0.2.0, cujo aplicador não guardava as notas
        # junto do pacote: a versão nova leva o resumo em version.json.
        try:
            versao_info = json.loads((raiz / "version.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None
        versao = str(versao_info.get("version", ""))
        tag = f"v{versao}"
        preferencias = QSettings("JARVIS", NOME_USUARIO or "JARVIS")
        ultima_notificada = str(preferencias.value("atualizacoes/ultima_versao_notificada", ""))
        ultima_anunciada = str(preferencias.value("atualizacoes/ultima_versao_anunciada", ""))
        if ultima_notificada.lstrip("vV") != versao or ultima_anunciada == tag:
            return None
        mudancas = str(versao_info.get("mudancas", "Melhorias e correções."))
        aprendizados = str(
            versao_info.get("aprendizados", "Nenhum aprendizado novo foi especificado.")
        )
        return {
            "versao": tag,
            "mudancas": mudancas,
            "aprendizados": aprendizados,
            "anunciada": False,
        }

    @staticmethod
    def _mensagem_abertura(aviso_atualizacao=None):
        hora = datetime.now().hour
        if 5 <= hora < 12:
            saudacao = "Bom dia"
        elif 12 <= hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"
        estado = obter_resumo_sistema()
        mensagem = (
            f"{saudacao}, senhor {NOME_USUARIO}. {estado} "
            "Estou à disposição por voz ou texto."
        )
        if aviso_atualizacao:
            versao = aviso_atualizacao.get("versao", "nova")
            mudancas = aviso_atualizacao.get("mudancas", "Melhorias e correções.")
            aprendizados = aviso_atualizacao.get(
                "aprendizados", "Nenhum aprendizado novo foi especificado."
            )
            mensagem += (
                f" Também atualizei para a versão {versao}. O que mudou: {mudancas}. "
                f"O conhecimento registrado nesta versão: {aprendizados}."
            )
        return mensagem

    def _marcar_atualizacao_anunciada(self):
        aviso = self.aviso_atualizacao
        if not aviso:
            return
        arquivo = Path(__file__).resolve().parents[1] / "dados" / "ultima_atualizacao.json"
        temporario = arquivo.with_suffix(".json.tmp")
        try:
            try:
                dados = json.loads(arquivo.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                dados = {}
            if not isinstance(dados, dict) or str(dados.get("versao", "")) != str(aviso.get("versao", "")):
                dados = {
                    "versao": aviso.get("versao", ""),
                    "mudancas": aviso.get("mudancas", ""),
                    "aprendizados": aviso.get("aprendizados", ""),
                }
            dados["anunciada"] = True
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
            temporario.replace(arquivo)
            preferencias = QSettings("JARVIS", NOME_USUARIO or "JARVIS")
            preferencias.setValue("atualizacoes/ultima_versao_anunciada", str(aviso.get("versao", "")))
            self._anunciar_atualizacao_na_abertura = False
        except (OSError, ValueError, TypeError) as erro:
            log(f"Não foi possível registrar o anúncio da atualização: {erro}")

    def _carregar_manchetes_iniciais(self):
        manchetes = carregar_manchetes(limite=3)
        descobertas = carregar_descobertas(limite=5)
        registrar_descobertas(descobertas)
        novas = []

        if descobertas is not None:
            preferencias = QSettings("JARVIS", NOME_USUARIO or "JARVIS")
            chave_vista = "novidades/descobertas_vistas"
            chave_iniciada = "novidades/primeira_consulta_concluida"
            conhecidas = set(preferencias.value(chave_vista, [], type=list))
            primeira_consulta = not preferencias.value(chave_iniciada, False, type=bool)
            identificadores = {
                f"{item.get('fonte', '')}|{item.get('titulo', '')}".casefold(): item
                for item in descobertas
                if isinstance(item, dict)
            }
            if not primeira_consulta:
                novas = [item for chave, item in identificadores.items() if chave not in conhecidas]
            conhecidas.update(identificadores)
            preferencias.setValue(chave_vista, sorted(conhecidas)[-100:])
            preferencias.setValue(chave_iniciada, True)

        self.manchetes_iniciais.emit(manchetes)
        self.descobertas_iniciais.emit(descobertas, novas)

    @Slot()
    def _solicitar_atualizacao_manchetes(self):
        if getattr(self, "thread_manchetes", None) and self.thread_manchetes.is_alive():
            return
        self.thread_manchetes = Thread(
            target=self._carregar_manchetes_iniciais,
            name="jarvis-atualizar-manchetes",
            daemon=True,
        )
        self.thread_manchetes.start()

    @Slot()
    def _solicitar_verificacao_atualizacao(self):
        if getattr(self, "thread_atualizacao", None) and self.thread_atualizacao.is_alive():
            return
        self.thread_atualizacao = Thread(
            target=self._verificar_atualizacao,
            name="jarvis-verificar-atualizacao",
            daemon=True,
        )
        self.thread_atualizacao.start()

    def _verificar_atualizacao(self):
        resultado = self.atualizador.verificar_e_preparar()
        self.atualizacao_inicial.emit(resultado)

    @Slot(object)
    def _receber_resultado_atualizacao(self, resultado):
        if resultado.get("status") == "pronta":
            self.atualizador.pacote_preparado = resultado.get("arquivo")
            preferencias = QSettings("JARVIS", NOME_USUARIO or "JARVIS")
            chave = "atualizacoes/ultima_versao_notificada"
            ultima_notificada = str(preferencias.value(chave, ""))
            resultado["avisar"] = ultima_notificada != resultado.get("versao")
            if resultado["avisar"]:
                preferencias.setValue(chave, resultado.get("versao", ""))
        self.janela.atualizar_status_atualizacao(resultado)

    # ==================================================
    # RECEBER COMANDO
    # ==================================================

    @Slot(str)
    def receber_comando(self, comando):

        if not comando:
            return

        print(f"\n👤 Você: {comando}")

        self.janela.adicionar_mensagem(
            "Você",
            comando
        )
        log(f"Comando por voz: {comando}")

        if comando.lower().strip() in [
            "sair",
            "fechar",
            "encerrar",
            "desligar",
            "tchau"
        ]:

            self.worker_audio.parar()
            self.janela.adicionar_mensagem("JARVIS", f"Até logo, senhor {NOME_USUARIO}.")
            log("J.A.R.V.I.S. encerrado pelo usuário.")
            self.app.quit()

    @Slot()
    def _ao_detectar_duas_palmas(self):
        if tocar_back_in_black():
            log("Gesto de duas palmas: reprodução de Back In Black solicitada ao Spotify.")
        else:
            log("Gesto de duas palmas detectado, mas o Spotify não foi iniciado.")
        QTimer.singleShot(1800, self._retomar_escuta_apos_gesto)

    @Slot()
    def _retomar_escuta_apos_gesto(self):
        self.worker_audio.definir_escuta(self.janela.microfone_ativo)

    @Slot(str)
    def receber_texto(self, texto):
        log(f"Mensagem digitada: {texto}")
        if texto.lower().strip() in {
            "sair", "fechar", "encerrar", "desligar", "tchau",
            "desligar jarvis", "fechar jarvis",
        }:
            self.janela.adicionar_mensagem("JARVIS", f"Até logo, senhor {NOME_USUARIO}.")
            QTimer.singleShot(250, self.app.quit)
            return
        self.worker_audio.definir_escuta(False)
        self.comando_manual.emit(texto)

    # ==================================================
    # RECEBER RESPOSTA
    # ==================================================

    @Slot(str)
    def receber_resposta(self, resposta):

        if not resposta:
            return

        print(f"\n🤖 Jarvis: {resposta}")
        log(f"JARVIS: {resposta}")

        self.janela.adicionar_mensagem(
            "Jarvis",
            resposta
        )

    # ==================================================
    # FIM DA FALA
    # ==================================================

    @Slot()
    def fala_terminou(self):

        if self._anunciar_atualizacao_na_abertura:
            self._marcar_atualizacao_anunciada()

        print("\n🎤 Pronto para ouvir novamente.")
        self.worker_audio.definir_escuta(self.janela.microfone_ativo)
        self.janela.estado_pronto()

    @Slot(str)
    def _erro_audio(self, erro):
        print(f"Erro no módulo de áudio: {erro}")
        self.worker_audio.definir_escuta(False)
        self.janela.marcar_microfone_indisponivel(erro)
        self.janela.estado_erro("Falha no áudio")

    @Slot(str)
    def _erro_ia(self, erro):
        print(f"Erro no módulo de inteligência: {erro}")
        self.janela.estado_erro("Falha na conexão com a IA")
        self.janela.definir_modulo(0, "IA INDISPONÍVEL", False)
        self.worker_audio.definir_escuta(self.janela.microfone_ativo)
        self.janela.adicionar_mensagem(
            "JARVIS",
            "Não consegui acessar o modelo local. Verifique se o Ollama está iniciado e se o modelo configurado está disponível.",
        )

    @Slot(str)
    def _erro_voz(self, erro):
        print(f"Erro no módulo de voz: {erro}")
        self.janela.estado_erro("Falha na síntese de voz")
        self.janela.definir_modulo(2, "VOZ INDISPONÍVEL", False)
        self.worker_audio.definir_escuta(self.janela.microfone_ativo)

    # ==================================================
    # INICIAR
    # ==================================================

    def iniciar(self):

        print("\n🚀 Iniciando threads...")

        # Evita que o microfone transcreva a própria saudação de abertura.
        self.worker_audio.definir_escuta(False)
        self.thread_ia.start()
        self.thread_voz.start()
        self.worker_audio.start()
        self.fala_solicitada.emit(self.mensagem_abertura)

        print("✓ Threads iniciadas.")
        print("✓ Saudação inicial enviada; o microfone será ativado ao terminar.\n")

        sys.exit(
            self.app.exec()
        )

    # ==================================================
    # ENCERRAR
    # ==================================================

    def encerrar(self):

        print("\nEncerrando JARVIS...")

        try:
            self.timer_manchetes.stop()
        except Exception:
            pass

        try:
            self.timer_atualizacao.stop()
        except Exception:
            pass

        try:
            self.worker_audio.parar()
        except Exception:
            pass

        try:
            self.thread_ia.quit()
            self.thread_ia.wait(2000)
        except Exception:
            pass

        try:
            self.thread_voz.quit()
            self.thread_voz.wait(2000)
        except Exception:
            pass

        try:
            self.voz.parar()
        except Exception:
            pass

        try:
            if self.atualizador.pacote_preparado and self.atualizador.agendar_aplicacao(os.getpid()):
                log("Nova versão preparada; será instalada ao fechar e o JARVIS reiniciará.")
        except Exception as erro:
            log(f"Não foi possível agendar a atualização: {erro}")

        print("✓ JARVIS finalizado.")


if __name__ == "__main__":

    jarvis = Assistente()
    jarvis.iniciar()
