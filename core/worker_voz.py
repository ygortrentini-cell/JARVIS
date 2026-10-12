from PySide6.QtCore import QObject, Signal, Slot


class WorkerVoz(QObject):
    falando = Signal()
    terminou = Signal()
    erro = Signal(str)

    def __init__(self, voz):
        super().__init__()
        self.voz = voz

    @Slot(str)
    def falar(self, texto):
        if not texto:
            return

        try:
            self.falando.emit()

            self.voz.falar(texto)

            self.terminou.emit()

        except Exception as e:
            print(f"Erro na voz: {e}")
            self.erro.emit(str(e))