import sounddevice as sd
import soundfile as sf
from pathlib import Path

arquivo = Path(__file__).with_name("teste.wav")

print("Fale durante 5 segundos...")

audio = sd.rec(
    int(5 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1
)

sd.wait()

sf.write(arquivo, audio, 16000)

print(f"Arquivo salvo em {arquivo}")
