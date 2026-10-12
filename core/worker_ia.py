from PySide6.QtCore import QObject, Signal, Slot


class WorkerIA(QObject):
    resposta = Signal(str)
    manchetes = Signal(object)
    pensando = Signal()
    erro = Signal(str)

    def __init__(self, inteligencia):
        super().__init__()
        self.inteligencia = inteligencia

    @Slot(str)
    def processar(self, comando):
        self._processar(comando, origem_voz=False)

    @Slot(str)
    def processar_voz(self, comando):
        self._processar(comando, origem_voz=True)

    def _processar(self, comando, origem_voz):
        if not comando:
            return

        try:
            self.pensando.emit()

            resposta = self.inteligencia.perguntar(comando, origem_voz=origem_voz)

            if getattr(self.inteligencia, "atualizou_manchetes", False):
                self.manchetes.emit(self.inteligencia.ultimas_manchetes)

            if resposta:
                self.resposta.emit(resposta)

        except Exception as e:
            print(f"Erro na inteligência: {e}")
            self.erro.emit(str(e))
