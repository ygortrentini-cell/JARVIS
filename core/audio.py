import time

import numpy as np
import config as configuracao

from config import (
    AUDIO_DEVICE,
    IDIOMA,
    LIMIAR_VOZ,
    MODELO_WHISPER,
    PAUSA_FINAL,
    TEMPO_GRAVACAO,
)
from modules.util import corrigir_transcricao


COMANDO_DUAS_PALMAS = "__JARVIS_DUAS_PALMAS__"
LIMIAR_PALMA_PICO = float(getattr(configuracao, "LIMIAR_PALMA_PICO", 0.16))
LIMIAR_PALMA_CREST = float(getattr(configuracao, "LIMIAR_PALMA_CREST", 3.5))
INTERVALO_PALMAS = float(getattr(configuracao, "INTERVALO_PALMAS", 1.0))


class Audio:

    def __init__(self):

        print("Carregando Whisper...")
        self.modelo = None
        self.sd = None
        self.erro = None

        try:
            import sounddevice as sd
            import whisper

            self.sd = sd
            self.modelo = whisper.load_model(MODELO_WHISPER)
            print("✓ Sistema de áudio carregado.")
        except Exception as erro:
            self.erro = str(erro)
            print(f"Áudio indisponível: {erro}")

    @property
    def disponivel(self):
        return self.modelo is not None and self.sd is not None

    @staticmethod
    def _pontuacao_transcricao(resultado):
        segmentos = resultado.get("segments") or []
        confiancas = [
            float(segmento["avg_logprob"])
            for segmento in segmentos
            if segmento.get("avg_logprob") is not None
        ]
        silencios = [
            float(segmento["no_speech_prob"])
            for segmento in segmentos
            if segmento.get("no_speech_prob") is not None
        ]
        if not confiancas:
            return None
        media = sum(confiancas) / len(confiancas)
        media_silencio = sum(silencios) / len(silencios) if silencios else 0.0
        return media - (0.25 * media_silencio)

    def ouvir(self):

        if not self.disponivel:
            raise RuntimeError(self.erro or "Os módulos de áudio não estão disponíveis.")

        print("\n🎤 Ouvindo...")
        taxa = 16000
        duracao_bloco = 0.05
        quadros_bloco = int(taxa * duracao_bloco)
        limiar_voz = LIMIAR_VOZ
        pausa_final = PAUSA_FINAL
        espera_inicial = 4.0
        blocos = []
        pre_audio = []
        falando = False
        silencio = 0.0
        ruido_ambiente = 0.0
        blocos_calibracao = 0
        inicio_gravacao = time.monotonic()
        primeira_palma = None

        # Mede o ruído do ambiente e guarda áudio anterior à fala para preservar
        # o começo de palavras, mesmo quando o volume da voz é baixo.
        with self.sd.InputStream(
            samplerate=taxa,
            channels=1,
            dtype="float32",
            device=AUDIO_DEVICE,
            blocksize=quadros_bloco,
        ) as stream:
            while time.monotonic() - inicio_gravacao < TEMPO_GRAVACAO:
                bloco, _ = stream.read(quadros_bloco)
                bloco = bloco.reshape(-1).copy()
                energia = float(np.sqrt(np.mean(bloco * bloco)))
                pico = float(np.max(np.abs(bloco)))

                if blocos_calibracao >= 6:
                    agora = time.monotonic()
                    limiar_pico = max(
                        LIMIAR_PALMA_PICO,
                        ruido_ambiente * 8,
                        limiar_voz * 30,
                    )
                    limiar_energia = max(0.018, ruido_ambiente * 3, limiar_voz * 2)
                    crista = pico / max(energia, 1e-6)
                    impulso = (
                        pico >= limiar_pico
                        and energia >= limiar_energia
                        and crista >= LIMIAR_PALMA_CREST
                    )
                    if impulso:
                        if primeira_palma is None or agora - primeira_palma > INTERVALO_PALMAS:
                            primeira_palma = agora
                        elif agora - primeira_palma >= 0.18:
                            print("👏👏 Duas palmas detectadas.")
                            return COMANDO_DUAS_PALMAS

                if not falando:
                    pre_audio.append(bloco)
                    pre_audio = pre_audio[-6:]

                    if blocos_calibracao < 6:
                        if energia < limiar_voz:
                            ruido_ambiente = (
                                energia
                                if blocos_calibracao == 0
                                else (ruido_ambiente * 0.7) + (energia * 0.3)
                            )
                        blocos_calibracao += 1
                    elif energia < limiar_voz:
                        ruido_ambiente = (ruido_ambiente * 0.95) + (energia * 0.05)

                    limiar_inicio = max(
                        limiar_voz,
                        min(ruido_ambiente * 1.8, limiar_voz * 1.25),
                    )
                    if energia >= limiar_inicio:
                        blocos.extend(pre_audio)
                        falando = True
                else:
                    blocos.append(bloco)
                    limiar_fim = max(
                        limiar_voz * 0.55,
                        min(ruido_ambiente * 1.25, limiar_voz * 0.9),
                    )
                    if energia < limiar_fim:
                        silencio += duracao_bloco
                    else:
                        silencio = 0.0

                    if silencio >= pausa_final:
                        break

                if (
                    not falando
                    and time.monotonic() - inicio_gravacao >= espera_inicial
                ):
                    break

        if not blocos:
            print("⚠ Nenhuma fala reconhecida.")
            return ""

        audio = np.concatenate(blocos).astype(np.float32, copy=False)
        tempo_gravacao = round(time.monotonic() - inicio_gravacao, 2)
        print(f"⏱ Tempo de gravação: {tempo_gravacao}s")

        inicio_whisper = time.monotonic()

        try:

            prompt = (
                "Conversa em português do Brasil. O assistente se chama Jarvis. "
                "Comandos e termos comuns: mostrar o sistema, consultar CPU, memória RAM, "
                "bateria e disco; me fale das notícias; abrir e fechar programas; "
                "abra o Brave e pesquise sobre algo; computador, Windows, Brave, Chrome, "
                "navegador, pesquisar, arquivos, código e sistema."
            )
            opcoes = {
                "language": IDIOMA,
                "fp16": False,
                "condition_on_previous_text": False,
                "initial_prompt": prompt,
            }
            resultado = self.modelo.transcribe(
                audio,
                **opcoes,
                temperature=(0.0, 0.2, 0.4),
            )

            pontuacao = self._pontuacao_transcricao(resultado)
            if not resultado.get("text", "").strip() or (
                pontuacao is not None and pontuacao < -0.75
            ):
                print("⚠ Transcrição incerta; tentando reconhecer a fala novamente.")
                try:
                    alternativa = self.modelo.transcribe(
                        audio,
                        **opcoes,
                        temperature=0.0,
                        beam_size=3,
                    )
                    pontuacao_alternativa = self._pontuacao_transcricao(alternativa)
                    if (
                        not resultado.get("text", "").strip()
                        or pontuacao_alternativa is not None
                        and (pontuacao is None or pontuacao_alternativa > pontuacao)
                    ):
                        resultado = alternativa
                except Exception as erro_retentativa:
                    print(f"⚠ Nova tentativa de transcrição indisponível: {erro_retentativa}")

            texto = corrigir_transcricao(resultado["text"].strip())

        except Exception as erro:

            print(f"❌ Erro no Whisper: {erro}")

            texto = ""

        finally:
            tempo_whisper = round(time.monotonic() - inicio_whisper, 2)

        print(f"🧠 Tempo do Whisper: {tempo_whisper}s")

        if texto:

            print(f"👤 Você: {texto}")

        else:

            print("⚠ Nenhuma fala reconhecida.")

        return texto
