from __future__ import annotations

from datetime import datetime
from html import escape
import math

try:
    import psutil
except ImportError:
    psutil = None
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QRectF, QLineF
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStyle,
    QSizePolicy,
    QSystemTrayIcon,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


FUNDO = "#071019"
PAINEL = "#0b1722"
BORDA = "#183447"
CIANO = "#53e6f2"
TEXTO = "#dcebf2"
SUAVE = "#7892a3"


class NucleoHolografico(QWidget):
    """Núcleo animado que muda de cor conforme o estado do assistente."""

    CORES = {
        "pronto": QColor("#48d9eb"),
        "ouvindo": QColor("#66f0cd"),
        "pensando": QColor("#ffbd62"),
        "falando": QColor("#64bcff"),
        "erro": QColor("#ff657a"),
        "pausado": QColor("#60798a"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.estado = "pronto"
        self.fase = 0
        self.animacao = QTimer(self)
        self.animacao.timeout.connect(self._animar)
        self.animacao.start(40)

    def definir_estado(self, estado: str):
        if estado in self.CORES:
            self.estado = estado
            self.update()

    def _animar(self):
        self.fase = (self.fase + 1) % 360
        self.update()

    def paintEvent(self, _event):
        lado = min(self.width(), self.height())
        centro_x = self.width() / 2
        centro_y = self.height() / 2
        raio = lado * 0.39
        cor = self.CORES[self.estado]
        pulso = 1 + 0.018 * (1 + math.sin(self.fase * 0.045))

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(centro_x, centro_y)

        halo = QRadialGradient(0, 0, raio * 1.55)
        halo.setColorAt(0, QColor(cor.red(), cor.green(), cor.blue(), 37))
        halo.setColorAt(0.58, QColor(cor.red(), cor.green(), cor.blue(), 12))
        halo.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(QRectF(-raio * 1.55, -raio * 1.55, raio * 3.1, raio * 3.1))

        painter.rotate(self.fase * 0.38)
        for index, span in enumerate((58, 42, 32, 24, 18, 12)):
            painter.save()
            painter.rotate(index * 60)
            alpha = 120 + (index % 3) * 38
            pen = QPen(QColor(cor.red(), cor.green(), cor.blue(), alpha), 2.1)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(
                QRectF(-raio, -raio, raio * 2, raio * 2),
                18 * 16,
                span * 16,
            )
            painter.restore()

        painter.rotate(-self.fase * 0.76)
        painter.setPen(QPen(QColor(cor.red(), cor.green(), cor.blue(), 66), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(-raio * 0.76, -raio * 0.76, raio * 1.52, raio * 1.52))

        nucleo_raio = raio * 0.53 * pulso
        brilho = QRadialGradient(-nucleo_raio * 0.2, -nucleo_raio * 0.26, nucleo_raio * 1.45)
        brilho.setColorAt(0, QColor("#e9ffff"))
        brilho.setColorAt(0.13, QColor(cor.red(), cor.green(), cor.blue(), 245))
        brilho.setColorAt(0.55, QColor(cor.red(), cor.green(), cor.blue(), 82))
        brilho.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(brilho)
        painter.drawEllipse(QRectF(-nucleo_raio * 1.45, -nucleo_raio * 1.45,
                                   nucleo_raio * 2.9, nucleo_raio * 2.9))

        painter.setBrush(QColor(7, 19, 29, 230))
        painter.setPen(QPen(QColor(cor.red(), cor.green(), cor.blue(), 200), 1.3))
        painter.drawEllipse(QRectF(-nucleo_raio * 0.72, -nucleo_raio * 0.72,
                                   nucleo_raio * 1.44, nucleo_raio * 1.44))

        painter.setPen(QPen(QColor(cor.red(), cor.green(), cor.blue(), 160), 1))
        for angle in range(0, 360, 30):
            painter.save()
            painter.rotate(angle)
            painter.drawLine(QLineF(0, -raio * 0.82, 0, -raio * 0.91))
            painter.restore()


class FundoHolografico(QWidget):
    """Fundo azul em grade, inspirado no painel exibido na referência."""

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradiente = QLinearGradient(0, 0, self.width(), self.height())
        gradiente.setColorAt(0, QColor("#071629"))
        gradiente.setColorAt(0.52, QColor("#092b57"))
        gradiente.setColorAt(1, QColor("#061321"))
        painter.fillRect(self.rect(), gradiente)

        halo = QRadialGradient(self.width() * 0.5, self.height() * 0.5, self.width() * 0.68)
        halo.setColorAt(0, QColor(19, 105, 205, 48))
        halo.setColorAt(0.65, QColor(8, 48, 104, 20))
        halo.setColorAt(1, QColor(4, 18, 40, 0))
        painter.fillRect(self.rect(), halo)

        painter.setPen(QPen(QColor(66, 169, 255, 28), 1))
        passo = 34
        for x in range(0, self.width(), passo):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), passo):
            painter.drawLine(0, y, self.width(), y)

        # Perspectiva discreta na base para a grade parecer uma superfície HUD.
        horizonte = int(self.height() * 0.70)
        painter.setPen(QPen(QColor(82, 187, 255, 34), 1))
        ponto_fuga = self.width() // 2
        for x in range(-self.width(), self.width() * 2, 110):
            painter.drawLine(ponto_fuga, horizonte, x, self.height())
        for indice in range(1, 8):
            proporcao = (indice / 7) ** 2
            y = horizonte + int((self.height() - horizonte) * proporcao)
            painter.drawLine(0, y, self.width(), y)


class JanelaJarvis(QMainWindow):
    enviar_comando = Signal(str)
    alternar_microfone = Signal(bool)
    imagem_manchete_carregada = Signal(str, bytes)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. | Interface de Operações")
        self.setMinimumSize(1120, 700)
        self.resize(1600, 950)
        self.setStyleSheet(
            f"QMainWindow {{ background: {FUNDO}; color: {TEXTO}; }}"
            "QLabel { background: transparent; }"
        )
        self._estado = "pronto"
        self._microfone_ativo = True
        self._url_imagem_atual = ""
        self._imagem_manchete = QPixmap()
        self.icone_bandeja = None
        self._construir_interface()
        self.imagem_manchete_carregada.connect(self._mostrar_imagem_manchete)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.icone_bandeja = QSystemTrayIcon(self)
            self.icone_bandeja.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
            self.icone_bandeja.setToolTip("J.A.R.V.I.S. · Assistente online")
            self.icone_bandeja.show()
        self._configurar_relogio()
        self._atualizar_metricas()

    def _construir_interface(self):
        raiz = FundoHolografico()
        raiz.setObjectName("raiz")
        layout_raiz = QVBoxLayout(raiz)
        layout_raiz.setContentsMargins(24, 18, 24, 14)
        layout_raiz.setSpacing(12)

        layout_raiz.addWidget(self._criar_cabecalho())

        corpo = QVBoxLayout()
        corpo.setSpacing(11)
        corpo.addWidget(self._criar_centro(), 6)
        corpo.addWidget(self._criar_coluna_sistema(), 2)
        corpo.addWidget(self._criar_conversa(), 1)
        layout_raiz.addLayout(corpo, 1)
        layout_raiz.addWidget(self._criar_rodape())
        self.setCentralWidget(raiz)

    def _criar_cabecalho(self):
        cabecalho = QFrame()
        cabecalho.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(cabecalho)
        layout.setContentsMargins(0, 0, 0, 7)

        marca = QLabel("J")
        marca.setFixedSize(43, 43)
        marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marca.setStyleSheet(
            f"color: {CIANO}; border: 1px solid #347588; border-radius: 21px;"
            "font-size: 23px; font-weight: 600; background: #0a202b;"
        )
        bloco_marca = QVBoxLayout()
        titulo = QLabel("J.A.R.V.I.S.")
        titulo.setStyleSheet("font-size: 18px; letter-spacing: 3px; font-weight: 700;")
        subtitulo = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM")
        subtitulo.setStyleSheet(f"font-size: 8px; letter-spacing: 1.6px; color: {SUAVE};")
        bloco_marca.addWidget(titulo)
        bloco_marca.addWidget(subtitulo)
        bloco_marca.setSpacing(3)

        identidade = QHBoxLayout()
        identidade.addWidget(marca)
        identidade.addSpacing(12)
        identidade.addLayout(bloco_marca)
        layout.addLayout(identidade)
        layout.addStretch(1)

        self.relogio = QLabel("--:--:--")
        self.relogio.setStyleSheet(f"color: {TEXTO}; font-size: 17px; font-weight: 600;")
        self.relogio.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.data = QLabel("INICIALIZANDO")
        self.data.setStyleSheet(f"color: {SUAVE}; font-size: 9px; letter-spacing: 1.5px;")
        self.data.setAlignment(Qt.AlignmentFlag.AlignRight)
        horario = QVBoxLayout()
        horario.setSpacing(2)
        horario.addWidget(self.relogio)
        horario.addWidget(self.data)
        layout.addLayout(horario)

        ponto = QLabel("  SISTEMA ATIVO")
        ponto.setStyleSheet(
            "color: #7cf0c6; font-size: 9px; letter-spacing: 1.2px;"
            "border: 1px solid #235344; border-radius: 10px; padding: 8px 11px;"
            "background: #0b211c;"
        )
        layout.addSpacing(24)
        layout.addWidget(ponto)
        return cabecalho

    def _painel(self, titulo: str, detalhe: str = ""):
        painel = QFrame()
        painel.setObjectName("painel")
        painel.setStyleSheet(
            "#painel { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            " stop:0 #0b2d58, stop:0.55 #082346, stop:1 #071b35);"
            f" border: 1px solid {BORDA}; border-radius: 13px; }}"
        )
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(17, 15, 17, 16)
        layout.setSpacing(12)
        cabecalho = QHBoxLayout()
        rotulo = QLabel(titulo.upper())
        rotulo.setStyleSheet(f"color: {TEXTO}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")
        cabecalho.addWidget(rotulo)
        cabecalho.addStretch(1)
        if detalhe:
            dica = QLabel(detalhe)
            dica.setStyleSheet(f"color: {SUAVE}; font-size: 9px;")
            cabecalho.addWidget(dica)
            if titulo.lower() == "módulos":
                self.modulos_online_label = dica
        layout.addLayout(cabecalho)
        return painel, layout

    def _criar_coluna_sistema(self):
        faixa = QWidget()
        layout = QHBoxLayout(faixa)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)

        painel, conteudo = self._painel("Telemetria", "AO VIVO")
        conteudo.setSpacing(7)
        self.cpu_valor, self.cpu_barra = self._linha_metrica(conteudo, "PROCESSADOR")
        self.ram_valor, self.ram_barra = self._linha_metrica(conteudo, "MEMÓRIA RAM")
        self.disco_valor, self.disco_barra = self._linha_metrica(conteudo, "ARMAZENAMENTO")
        painel_telemetria = painel
        layout.addWidget(painel, 1)

        painel, conteudo = self._painel("Últimas notícias", "AO VIVO")
        conteudo.setSpacing(8)
        self.status_outras_noticias = QLabel("Carregando manchetes...")
        self.status_outras_noticias.setStyleSheet(f"color: {SUAVE}; font-size: 8px;")
        conteudo.addWidget(self.status_outras_noticias)
        self.manchetes_secundarias = []
        for _ in range(2):
            manchete = QLabel("Aguardando o feed de notícias.")
            manchete.setTextFormat(Qt.TextFormat.PlainText)
            manchete.setWordWrap(True)
            manchete.setStyleSheet(
                "color: #e1f0fc; background: #0a2a4e; border: 1px solid #1b527d;"
                " border-radius: 7px; padding: 8px 9px; font-size: 9px; font-weight: 600;"
            )
            conteudo.addWidget(manchete, 1)
            self.manchetes_secundarias.append(manchete)
        layout.addWidget(painel, 1)

        painel, conteudo = self._painel("Descobertas", "CIÊNCIA & TECNOLOGIA")
        conteudo.setSpacing(8)
        self.status_descobertas = QLabel("Buscando novas publicações...")
        self.status_descobertas.setWordWrap(True)
        self.status_descobertas.setStyleSheet(f"color: {SUAVE}; font-size: 8px;")
        conteudo.addWidget(self.status_descobertas)
        self.descobertas_labels = []
        for _ in range(3):
            descoberta = QLabel("Aguardando os feeds de pesquisa.")
            descoberta.setTextFormat(Qt.TextFormat.PlainText)
            descoberta.setWordWrap(True)
            descoberta.setStyleSheet(
                "color: #e1f0fc; background: #0a2a4e; border: 1px solid #1b527d;"
                " border-radius: 7px; padding: 8px 9px; font-size: 9px; font-weight: 600;"
            )
            conteudo.addWidget(descoberta, 1)
            self.descobertas_labels.append(descoberta)
        layout.addWidget(painel, 1)

        self.modulos = []
        self._modulos_online = [True, True, True, True]
        for nome, valor in (("NÚCLEO DE IA", "OLLAMA"), ("RECONHECIMENTO", "WHISPER"),
                            ("SÍNTESE DE VOZ", "ATIVO"), ("MEMÓRIA", "LOCAL")):
            estado_lbl = QLabel("●  " + valor)
            estado_lbl.setToolTip(nome)
            estado_lbl.setStyleSheet("color: #7ce4c1; font-size: 8px; letter-spacing: .5px;")
            self.modulos.append(estado_lbl)
        self.modulos_online_label = QLabel("4 / 4 MÓDULOS ATIVOS")
        self.modulos_online_label.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: .5px;")
        painel_telemetria.layout().addWidget(self.modulos_online_label)
        linha_modulos = QHBoxLayout()
        for estado_lbl in self.modulos:
            linha_modulos.addWidget(estado_lbl)
        painel_telemetria.layout().addLayout(linha_modulos)
        return faixa

    def _linha_metrica(self, layout, nome):
        linha = QHBoxLayout()
        label = QLabel(nome)
        label.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: 1px;")
        valor = QLabel("--%")
        valor.setStyleSheet(f"color: {CIANO}; font-size: 10px; font-weight: 700;")
        linha.addWidget(label)
        linha.addStretch(1)
        linha.addWidget(valor)
        layout.addLayout(linha)
        barra = QProgressBar()
        barra.setRange(0, 100)
        barra.setValue(0)
        barra.setTextVisible(False)
        barra.setFixedHeight(5)
        barra.setStyleSheet(
            "QProgressBar { background: #132634; border: 0; border-radius: 2px; }"
            f"QProgressBar::chunk {{ background: {CIANO}; border-radius: 2px; }}"
        )
        layout.addWidget(barra)
        return valor, barra

    def _criar_centro(self):
        centro = QWidget()
        layout = QHBoxLayout(centro)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(13)

        painel_nucleo = QFrame()
        painel_nucleo.setObjectName("painelNucleo")
        painel_nucleo.setStyleSheet(
            "QFrame#painelNucleo { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            " stop:0 #0b2e59, stop:0.52 #082348, stop:1 #07172f);"
            " border: 1px solid #2371a8; border-radius: 15px; }"
        )
        conteudo_nucleo = QVBoxLayout(painel_nucleo)
        conteudo_nucleo.setContentsMargins(19, 16, 19, 17)
        conteudo_nucleo.setSpacing(8)

        abertura = QLabel("NÚCLEO J.A.R.V.I.S.")
        abertura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        abertura.setStyleSheet(
            f"color: {TEXTO}; font-size: 11px; font-weight: 700; letter-spacing: 2px;"
        )
        descricao = QLabel("CENTRAL HOLOGRÁFICA  /  SISTEMA ONLINE")
        descricao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descricao.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: 1px;")
        conteudo_nucleo.addWidget(abertura)
        conteudo_nucleo.addWidget(descricao)
        conteudo_nucleo.addStretch(1)

        self.nucleo = NucleoHolografico()
        self.nucleo.setFixedSize(224, 224)
        conteudo_nucleo.addWidget(self.nucleo, 0, Qt.AlignmentFlag.AlignHCenter)

        self.estado = QLabel("TODOS OS SISTEMAS PRONTOS")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            f"color: {CIANO}; font-size: 14px; letter-spacing: 2px; font-weight: 700;"
        )
        conteudo_nucleo.addWidget(self.estado)

        self.botao_microfone = QPushButton("◉  MICROFONE ATIVO")
        self.botao_microfone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_microfone.setMinimumHeight(38)
        self.botao_microfone.clicked.connect(self._alternar_microfone)
        self.botao_microfone.setStyleSheet(
            "QPushButton { color: #9bead6; background: #0b211d; border: 1px solid #28614f;"
            " border-radius: 8px; padding: 0 17px; font-size: 9px; font-weight: 700; letter-spacing: 1px; }"
            "QPushButton:hover { background: #102f28; }"
        )
        conteudo_nucleo.addStretch(1)
        conteudo_nucleo.addWidget(self.botao_microfone)
        layout.addWidget(painel_nucleo, 2)

        painel = QFrame()
        painel.setObjectName("noticiaPrincipal")
        painel.setStyleSheet(
            "QFrame#noticiaPrincipal { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            " stop:0 #0b3263, stop:0.55 #08264e, stop:1 #071a36);"
            " border: 1px solid #2371a8; border-radius: 15px; }"
        )
        artigo = QVBoxLayout(painel)
        artigo.setContentsMargins(15, 13, 15, 14)
        artigo.setSpacing(8)

        faixa = QHBoxLayout()
        self.categoria_manchete = QLabel("AGÊNCIA BRASIL  /  DESTAQUE")
        self.categoria_manchete.setTextFormat(Qt.TextFormat.PlainText)
        self.categoria_manchete.setStyleSheet(f"color: {CIANO}; font-size: 8px; font-weight: 700; letter-spacing: 1.2px;")
        self.status_manchetes = QLabel("BUSCANDO NOTÍCIAS ATUAIS")
        self.status_manchetes.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: .5px;")
        faixa.addWidget(self.categoria_manchete)
        faixa.addStretch(1)
        faixa.addWidget(self.status_manchetes)
        artigo.addLayout(faixa)

        self.imagem_manchete = QLabel("SINAL DE NOTÍCIAS\nAGUARDANDO DADOS ATUAIS")
        self.imagem_manchete.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagem_manchete.setMinimumHeight(175)
        self.imagem_manchete.setMaximumHeight(350)
        self.imagem_manchete.setStyleSheet(
            "color: #71cfff; background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            " stop:0 #164d8c, stop:0.5 #08244b, stop:1 #06162e);"
            " border: 1px solid #1c5a91; border-radius: 10px; font-size: 10px;"
            " font-weight: 700; letter-spacing: 2px;"
        )
        self.imagem_manchete.setScaledContents(False)
        artigo.addWidget(self.imagem_manchete, 1)

        self.titulo_manchete = QLabel("Carregando o destaque mais recente...")
        self.titulo_manchete.setTextFormat(Qt.TextFormat.PlainText)
        self.titulo_manchete.setWordWrap(True)
        self.titulo_manchete.setMinimumHeight(48)
        self.titulo_manchete.setStyleSheet(f"color: #f1f8ff; font-size: 19px; font-weight: 700;")
        artigo.addWidget(self.titulo_manchete)

        self.resumo_manchete = QLabel("As manchetes são obtidas do feed atual da Agência Brasil.")
        self.resumo_manchete.setTextFormat(Qt.TextFormat.PlainText)
        self.resumo_manchete.setWordWrap(True)
        self.resumo_manchete.setMaximumHeight(43)
        self.resumo_manchete.setStyleSheet(f"color: #b8d0e3; font-size: 9px;")
        artigo.addWidget(self.resumo_manchete)

        rodape_artigo = QHBoxLayout()
        self.fonte_manchete = QLabel("FONTE  /  AGÊNCIA BRASIL")
        self.fonte_manchete.setTextFormat(Qt.TextFormat.PlainText)
        self.fonte_manchete.setStyleSheet(f"color: #82a9c7; font-size: 8px; letter-spacing: .8px;")
        rodape_artigo.addWidget(self.fonte_manchete, 1)
        self.botao_abrir_manchete = QPushButton("ABRIR MATÉRIA ↗")
        self.botao_abrir_manchete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_abrir_manchete.setEnabled(False)
        self.botao_abrir_manchete.clicked.connect(self._abrir_manchete)
        self.botao_abrir_manchete.setStyleSheet(
            "QPushButton { color: #a8edff; background: #0a3766; border: 1px solid #2878ac;"
            " border-radius: 6px; padding: 7px 11px; font-size: 8px; font-weight: 700; }"
            "QPushButton:hover { background: #10518b; }"
            "QPushButton:disabled { color: #668399; background: #0a223d; border-color: #1c3b56; }"
        )
        rodape_artigo.addWidget(self.botao_abrir_manchete)
        artigo.addLayout(rodape_artigo)
        layout.addWidget(painel, 3)
        return centro

    def _criar_conversa(self):
        coluna = QWidget()
        layout = QVBoxLayout(coluna)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        painel, conteudo = self._painel("Comunicação com JARVIS", "VOZ / TEXTO")
        self.conversa = QTextBrowser()
        self.conversa.setOpenExternalLinks(False)
        self.conversa.setStyleSheet(
            "QTextBrowser { background: transparent; border: none; color: #dcebf2;"
            " font-size: 10px; padding: 0; }"
            "QScrollBar:vertical { background: transparent; width: 5px; margin: 0; }"
            "QScrollBar::handle:vertical { background: #28495a; border-radius: 2px; min-height: 22px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        self.conversa.setPlaceholderText("Aguardando comunicação...")
        self.conversa.setMinimumHeight(38)
        self.conversa.setMaximumHeight(52)
        conteudo.addWidget(self.conversa, 1)

        entrada = QHBoxLayout()
        self.campo_mensagem = QLineEdit()
        self.campo_mensagem.setPlaceholderText("Fale com o JARVIS...")
        self.campo_mensagem.setMinimumHeight(43)
        self.campo_mensagem.returnPressed.connect(self._enviar_mensagem)
        self.campo_mensagem.setStyleSheet(
            "QLineEdit { color: #e4f3f8; background: #08121b; border: 1px solid #234355;"
            " border-radius: 8px; padding: 0 12px; font-size: 10px; }"
            f"QLineEdit:focus {{ border: 1px solid {CIANO}; }}"
        )
        enviar = QPushButton("ENVIAR")
        enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        enviar.setMinimumHeight(43)
        enviar.clicked.connect(self._enviar_mensagem)
        enviar.setStyleSheet(
            f"QPushButton {{ color: #061117; background: {CIANO}; border: none; border-radius: 8px;"
            " padding: 0 13px; font-size: 9px; font-weight: 800; letter-spacing: .7px; }"
            "QPushButton:hover { background: #8cf4fc; }"
        )
        entrada.addWidget(self.campo_mensagem, 1)
        entrada.addWidget(enviar)
        conteudo.addLayout(entrada)
        layout.addWidget(painel, 1)
        return coluna

    @Slot(object)
    def atualizar_manchetes(self, manchetes):
        if manchetes is None:
            if not getattr(self, "_artigos_manchetes", None):
                self.status_manchetes.setText("SEM CONEXÃO COM O FEED")
                self.titulo_manchete.setText("Não foi possível carregar as notícias agora.")
                self.resumo_manchete.setText("O JARVIS tentará atualizar novamente em breve.")
            else:
                self.status_manchetes.setText("FALHA NA ATUALIZAÇÃO · MANTENDO AS ÚLTIMAS")
            return

        resultados = []
        for item in manchetes:
            if isinstance(item, dict):
                artigo = dict(item)
            else:
                artigo = {"titulo": str(item).strip(), "fonte": "Agência Brasil"}
            if artigo.get("titulo"):
                resultados.append(artigo)
        if not resultados:
            self.status_manchetes.setText("NENHUMA MATÉRIA DISPONÍVEL")
            return

        self._artigos_manchetes = resultados
        self.status_manchetes.setText(f"ATUALIZADO · {datetime.now().strftime('%H:%M')}")
        principal = resultados[0]
        titulo = principal.get("titulo", "")
        self.titulo_manchete.setText(titulo)
        self.resumo_manchete.setText(
            principal.get("resumo") or "Acesse a matéria para ler todos os detalhes."
        )
        fonte = principal.get("fonte") or "Agência Brasil"
        publicado = principal.get("publicado", "")
        self.fonte_manchete.setText(
            f"FONTE  /  {fonte.upper()}" + (f"  ·  {publicado}" if publicado else "")
        )
        categoria = principal.get("categoria") or "Destaque"
        self.categoria_manchete.setText(f"{fonte.upper()}  /  {categoria.upper()}")
        self._link_manchete = principal.get("link", "")
        self.botao_abrir_manchete.setEnabled(bool(self._link_manchete))

        self._url_imagem_atual = principal.get("imagem", "")
        self._imagem_manchete = QPixmap()
        self.imagem_manchete.clear()
        if self._url_imagem_atual:
            self.imagem_manchete.setText("CARREGANDO IMAGEM DA MATÉRIA...")
            self._carregar_imagem_manchete(self._url_imagem_atual)
        else:
            self.imagem_manchete.setText("ATUALIZAÇÃO AO VIVO  /  AGÊNCIA BRASIL")

        for indice, cartao in enumerate(self.manchetes_secundarias):
            artigo = resultados[indice + 1] if indice + 1 < len(resultados) else None
            if artigo:
                cartao.setText(f"{indice + 2:02d}  /  {artigo['titulo']}")
                cartao.setToolTip(artigo.get("resumo", ""))
            else:
                cartao.setText("Nenhuma outra manchete disponível neste momento.")

        self.status_outras_noticias.setText(
            f"{len(resultados)} manchetes · feed atualizado às {datetime.now().strftime('%H:%M')}"
        )

    @Slot(object, object)
    def atualizar_descobertas(self, descobertas, novas=False):
        if descobertas is None:
            if not getattr(self, "_descobertas_atuais", None):
                self.status_descobertas.setText("Feeds de pesquisa indisponíveis no momento.")
            return

        artigos = [
            dict(item) for item in descobertas
            if isinstance(item, dict) and item.get("titulo")
        ]
        if not artigos:
            self.status_descobertas.setText("Nenhuma publicação nova nos feeds acompanhados.")
            return

        self._descobertas_atuais = artigos
        horario = datetime.now().strftime("%H:%M")
        for indice, cartao in enumerate(self.descobertas_labels):
            if indice < len(artigos):
                artigo = artigos[indice]
                cartao.setText(f"{artigo.get('fonte', 'Pesquisa')}  /  {artigo['titulo']}")
                cartao.setToolTip(artigo.get("resumo", ""))
            else:
                cartao.setText("Sem outra descoberta em destaque.")
        if len(artigos) > len(self.descobertas_labels):
            resumo_completo = "\n".join(item["titulo"] for item in artigos)
            self.descobertas_labels[-1].setToolTip(resumo_completo)

        if novas:
            quantidade = len(novas) if isinstance(novas, (list, tuple)) else 1
            self.status_descobertas.setText(f"{quantidade} NOVA(S) DESCOBERTA(S) · {horario}")
            lista_novas = novas if isinstance(novas, (list, tuple)) else artigos
            titulos = [item.get("titulo", "") for item in lista_novas[:2] if isinstance(item, dict)]
            resumo = "\n".join(titulos) or "Há novas publicações nos feeds de pesquisa."
            if self.icone_bandeja:
                self.icone_bandeja.showMessage(
                    "J.A.R.V.I.S. encontrou novidades",
                    resumo,
                    QSystemTrayIcon.MessageIcon.Information,
                    9000,
                )
        else:
            self.status_descobertas.setText(
                f"{len(artigos)} publicações acompanhadas · atualizado às {horario}"
            )

    def _carregar_imagem_manchete(self, url):
        from threading import Thread
        import urllib.request

        def buscar():
            dados = b""
            try:
                pedido = urllib.request.Request(
                    url, headers={"User-Agent": "JarvisAssistente/1.0"}
                )
                with urllib.request.urlopen(pedido, timeout=5) as resposta:
                    dados = resposta.read(5_000_000)
            except (OSError, ValueError):
                pass
            self.imagem_manchete_carregada.emit(url, dados)

        Thread(target=buscar, name="jarvis-imagem-noticia", daemon=True).start()

    @Slot(str, bytes)
    def _mostrar_imagem_manchete(self, url, dados):
        if url != self._url_imagem_atual or not dados:
            if url == self._url_imagem_atual and not dados:
                self.imagem_manchete.setText("IMAGEM INDISPONÍVEL  /  MATÉRIA ATUALIZADA")
            return
        imagem = QPixmap()
        if imagem.loadFromData(dados):
            self._imagem_manchete = imagem
            self._ajustar_imagem_manchete()

    def _ajustar_imagem_manchete(self):
        if (
            hasattr(self, "imagem_manchete")
            and hasattr(self, "_imagem_manchete")
            and not self._imagem_manchete.isNull()
        ):
            self.imagem_manchete.setText("")
            self.imagem_manchete.setPixmap(
                self._imagem_manchete.scaled(
                    self.imagem_manchete.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _abrir_manchete(self):
        import webbrowser

        link = getattr(self, "_link_manchete", "")
        if link:
            webbrowser.open_new_tab(link)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajustar_imagem_manchete()

    def _criar_rodape(self):
        rodape = QFrame()
        rodape.setStyleSheet("background: transparent; border-top: 1px solid #142a38;")
        layout = QHBoxLayout(rodape)
        layout.setContentsMargins(2, 11, 2, 0)
        self.rodape_status = QLabel("PROCESSAMENTO LOCAL  •  INTERFACE PRONTA")
        self.rodape_status.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: 1.2px;")
        self.status_atualizacao = QLabel("ATUALIZADOR  /  VERIFICANDO GITHUB")
        self.status_atualizacao.setStyleSheet(f"color: {SUAVE}; font-size: 8px; letter-spacing: .8px;")
        versao = QLabel("J.A.R.V.I.S.  /  INTERFACE DE OPERAÇÕES")
        versao.setStyleSheet(f"color: #476272; font-size: 8px; letter-spacing: 1px;")
        layout.addWidget(self.rodape_status)
        layout.addStretch(1)
        layout.addWidget(self.status_atualizacao)
        layout.addSpacing(20)
        layout.addWidget(versao)
        return rodape

    @Slot(object)
    def atualizar_status_atualizacao(self, resultado):
        status = resultado.get("status")
        atual = resultado.get("atual", "")
        versao = resultado.get("versao", "")
        mensagens = {
            "sem_release": f"JARVIS v{atual}  /  AGUARDANDO PRIMEIRA RELEASE",
            "atualizado": f"JARVIS v{atual}  /  ATUALIZADO",
            "pronta": f"VERSÃO {versao} PRONTA  /  APLICAR AO FECHAR",
            "release_incompleta": f"VERSÃO {versao}  /  PACOTE DE ATUALIZAÇÃO AUSENTE",
            "erro": "ATUALIZADOR  /  NOVA TENTATIVA PROGRAMADA",
        }
        texto = mensagens.get(status, "ATUALIZADOR  /  AGUARDANDO")
        self.status_atualizacao.setText(texto)
        self.status_atualizacao.setToolTip(resultado.get("notas") or resultado.get("detalhe", ""))

        if status == "pronta" and resultado.get("avisar") and self.icone_bandeja:
            novidades = resultado.get("notas") or "Novidades e correções desta versão."
            self.icone_bandeja.showMessage(
                f"J.A.R.V.I.S. · atualização {versao}",
                f"Baixada e validada. Será instalada ao fechar; o JARVIS abrirá atualizado.\n{novidades[:180]}",
                QSystemTrayIcon.MessageIcon.Information,
                12000,
            )

    def _configurar_relogio(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._atualizar_relogio)
        self.timer.timeout.connect(self._atualizar_metricas)
        self.timer.start(1000)
        self._atualizar_relogio()

    def _atualizar_relogio(self):
        agora = datetime.now()
        self.relogio.setText(agora.strftime("%H:%M:%S"))
        dias = ("SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO")
        meses = ("JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ")
        self.data.setText(
            f"{dias[agora.weekday()]}  /  {agora.day:02d} {meses[agora.month - 1]} {agora.year}"
        )

    def _atualizar_metricas(self):
        if psutil is None:
            self.cpu_valor.setText("N/D")
            self.ram_valor.setText("N/D")
            self.disco_valor.setText("N/D")
            return
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage("C:\\").percent
        self.cpu_valor.setText(f"{cpu:.0f}%")
        self.cpu_barra.setValue(int(cpu))
        self.ram_valor.setText(f"{ram:.0f}%")
        self.ram_barra.setValue(int(ram))
        self.disco_valor.setText(f"{disco:.0f}%")
        self.disco_barra.setValue(int(disco))

    def _alternar_microfone(self):
        self._microfone_ativo = not self._microfone_ativo
        estado = self._microfone_ativo
        self.botao_microfone.setText("  MICROFONE ATIVO" if estado else "  MICROFONE PAUSADO")
        cor = "#9bead6" if estado else "#9bb0bd"
        fundo = "#0b211d" if estado else "#17212a"
        borda = "#28614f" if estado else "#354754"
        self.botao_microfone.setStyleSheet(
            f"QPushButton {{ color: {cor}; background: {fundo}; border: 1px solid {borda};"
            " border-radius: 8px; padding: 0 17px; font-size: 9px; font-weight: 700; letter-spacing: 1px; }"
            "QPushButton:hover { background: #102f28; }"
        )
        self.alternar_microfone.emit(estado)
        if estado:
            self.estado_ouvindo()
        else:
            self.estado_pronto("MICROFONE EM PAUSA")

    def marcar_microfone_indisponivel(self, detalhe=""):
        self._microfone_ativo = False
        self.botao_microfone.setText("  MICROFONE INDISPONÍVEL")
        self.botao_microfone.setEnabled(False)
        self.botao_microfone.setStyleSheet(
            "QPushButton { color: #8a9ca7; background: #17212a; border: 1px solid #354754;"
            " border-radius: 8px; padding: 0 17px; font-size: 9px; font-weight: 700; letter-spacing: 1px; }"
        )
        if detalhe:
            self.rodape_status.setText(f"ÁUDIO INDISPONÍVEL: {escape(str(detalhe))[:70]}")
        self.definir_modulo(1, "ÁUDIO INDISPONÍVEL", False)
        self.estado_pronto("MODO DE TEXTO DISPONÍVEL")

    @property
    def microfone_ativo(self):
        return self._microfone_ativo

    def definir_modulo(self, indice, texto, online):
        if not 0 <= indice < len(self.modulos):
            return
        self._modulos_online[indice] = online
        self.modulos[indice].setText("●  " + texto)
        cor = "#7ce4c1" if online else "#f18b91"
        self.modulos[indice].setStyleSheet(
            f"color: {cor}; font-size: 8px; letter-spacing: .5px;"
        )
        total = sum(self._modulos_online)
        self.modulos_online_label.setText(f"{total} / 4 ATIVOS")

    def _enviar_mensagem(self):
        mensagem = self.campo_mensagem.text().strip()
        if not mensagem:
            return
        self.campo_mensagem.clear()
        self.adicionar_mensagem("Você", mensagem)
        self.enviar_comando.emit(mensagem)

    def adicionar_mensagem(self, autor, mensagem):
        cor_autor = "#54dce9" if autor.lower() in {"jarvis", "assistente"} else "#a7c2d0"
        texto = escape(str(mensagem)).replace("\n", "<br>")
        horario = datetime.now().strftime("%H:%M")
        self.conversa.append(
            f'<div style="margin: 8px 0 13px;">'
            f'<span style="color:{cor_autor}; font-size:9px; font-weight:700; letter-spacing:1px;">'
            f'{escape(str(autor).upper())}</span>'
            f'<span style="color:#536c7b; font-size:8px;">  {horario}</span>'
            f'<div style="color:#d9e8ef; margin-top:4px; line-height:1.5;">{texto}</div></div>'
        )
        barra = self.conversa.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _definir_estado(self, estado, texto, cor=None):
        self._estado = estado
        self.nucleo.definir_estado(estado)
        self.estado.setText(texto)
        cor = cor or self.nucleo.CORES[estado].name()
        self.estado.setStyleSheet(
            f"color: {cor}; font-size: 14px; letter-spacing: 2px; font-weight: 700;"
        )

    def estado_pronto(self, texto="TODOS OS SISTEMAS PRONTOS"):
        estado = "pronto" if self._microfone_ativo else "pausado"
        self._definir_estado(estado, texto)

    def estado_ouvindo(self):
        if self._microfone_ativo:
            self._definir_estado("ouvindo", "ESCUTANDO")

    def estado_pensando(self):
        self._definir_estado("pensando", "PROCESSANDO")

    def estado_falando(self):
        self._definir_estado("falando", "FALANDO")

    def estado_erro(self, detalhe=""):
        self._definir_estado("erro", "ATENÇÃO: FALHA NO SISTEMA")
        if detalhe:
            self.rodape_status.setText(f"SISTEMA: {escape(str(detalhe))[:90]}")

