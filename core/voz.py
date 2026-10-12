import json
import io
import subprocess
import wave
from pathlib import Path

from config import VELOCIDADE_VOZ, TONALIDADE_VOZ


class Voz:
    """Síntese Piper local, com fallback para o sintetizador do Windows."""

    def __init__(self):
        self.processo = None
        self.script = Path(__file__).with_name("voz_windows.ps1")
        pasta_modelos = Path(__file__).parents[1] / "assets" / "voz"
        self.modelos_piper = [
            ("Cadu", pasta_modelos / "pt_BR-cadu-medium.onnx"),
            ("Faber", pasta_modelos / "pt_BR-faber-medium.onnx"),
        ]
        self.voz_piper = None
        self.config_sintese = None
        self.nome_voz_piper = None
        self._piper_tentado = False
        print("✓ Sistema de voz carregado.")

    def _carregar_piper(self):
        if self._piper_tentado:
            return self.voz_piper is not None

        self._piper_tentado = True
        try:
            from piper import PiperVoice
            from piper.config import SynthesisConfig
        except Exception as erro:
            print(f"⚠ Não foi possível iniciar o Piper: {erro}")
            return False

        for nome, modelo in self.modelos_piper:
            config = modelo.with_suffix(modelo.suffix + ".json")
            if not modelo.is_file() or not config.is_file():
                continue

            try:
                self.voz_piper = PiperVoice.load(
                    str(modelo), config_path=str(config)
                )
                velocidade = max(float(VELOCIDADE_VOZ), 0.1)
                self.config_sintese = SynthesisConfig(length_scale=1.0 / velocidade)
                self.nome_voz_piper = nome
                print(f"✓ Voz neural Piper {nome} carregada.")
                return True
            except Exception as erro:
                print(f"⚠ Não foi possível carregar a voz Piper {nome}: {erro}")

        self.voz_piper = None
        return False

    def _falar_piper(self, texto):
        import sounddevice as sd
        import soundfile as sf

        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, "wb") as arquivo_audio:
            self.voz_piper.synthesize_wav(
                texto, arquivo_audio, syn_config=self.config_sintese
            )

        audio_buffer.seek(0)
        audio, taxa = sf.read(audio_buffer, dtype="float32")
        sd.play(audio, taxa)
        sd.wait()

    def _falar_windows(self, texto):
        if self.processo is None or self.processo.poll() is not None:
            self._iniciar()

        pedido = json.dumps(
            {
                "texto": texto,
                "velocidade": VELOCIDADE_VOZ,
                "tonalidade": TONALIDADE_VOZ,
            },
            ensure_ascii=False,
        )
        self.processo.stdin.write(pedido + "\n")
        self.processo.stdin.flush()

        resultado = self.processo.stdout.readline().strip()
        if resultado != "OK":
            raise RuntimeError(resultado.removeprefix("ERROR:").strip() or "Falha ao sintetizar a fala.")

    def _iniciar(self):
        self.processo = subprocess.Popen(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-STA",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.script),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        pronto = self.processo.stdout.readline().strip()
        if pronto != "READY":
            self._encerrar_processo()
            raise RuntimeError(pronto or "O sintetizador de voz do Windows não iniciou.")

    def falar(self, texto):
        if not texto:
            return

        print(f"\n🤖 Jarvis: {texto}")

        if self._carregar_piper():
            try:
                self._falar_piper(texto)
                return
            except Exception as erro:
                print(f"⚠ A voz Piper falhou; usando a voz do Windows: {erro}")
                self.voz_piper = None

        self._falar_windows(texto)

    def _encerrar_processo(self):
        if self.processo is None:
            return

        try:
            if self.processo.poll() is None:
                self.processo.terminate()
                self.processo.wait(timeout=2)
        except Exception:
            pass
        finally:
            self.processo = None

    def parar(self):
        if self.voz_piper is not None:
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:
                pass
        self._encerrar_processo()
