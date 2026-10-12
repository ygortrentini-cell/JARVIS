from PySide6.QtCore import QThread, Signal
import time

from core.audio import COMANDO_DUAS_PALMAS


class WorkerAudio(QThread):

    # Envia o texto reconhecido para o restante do Jarvis
    comando = Signal(str)
    gesto_palmas = Signal()

    # Informa à interface que começou a ouvir
    ouvindo = Signal()

    # Informa quando aconteceu um erro
    erro = Signal(str)

    def __init__(self, audio):

        super().__init__()

        self.audio = audio
        self.ativo = True
        self.habilitado = audio.disponivel

    def run(self):

        while self.ativo:

            try:

                if not self.habilitado:
                    time.sleep(0.1)
                    continue

                # Avisar a interface
                self.ouvindo.emit()

                # Ouvir pelo módulo Audio
                texto = self.audio.ouvir()

                # Se reconheceu alguma coisa
                if texto and self.habilitado and self.ativo:

                    if texto == COMANDO_DUAS_PALMAS:
                        self.gesto_palmas.emit()
                    else:
                        self.comando.emit(texto)
                    self.habilitado = False

                # Pequena pausa para evitar loop excessivamente rápido
                time.sleep(0.1)

            except Exception as e:

                print(f"Erro no áudio: {e}")

                self.erro.emit(str(e))

                time.sleep(1)

    def parar(self):

        self.ativo = False

        self.quit()

        self.wait()

    def definir_escuta(self, habilitado):
        self.habilitado = bool(habilitado)
