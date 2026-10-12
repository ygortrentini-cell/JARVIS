# Modelo de configuração. Copie para config.py e ajuste as opções do seu PC.
NOME_ASSISTENTE = "Jarvis"
NOME_USUARIO = "Usuário"
MODELO_IA = "qwen3.5:4b"
IDIOMA = "pt"

# None seleciona o microfone padrão do Windows.
AUDIO_DEVICE = None
MODELO_WHISPER = "small"
TEMPO_GRAVACAO = 25
LIMIAR_VOZ = 0.0035
PAUSA_FINAL = 1.15
# Duas palmas: ajuste o pico para cima se ruídos ativarem o gesto por engano.
LIMIAR_PALMA_PICO = 0.16
LIMIAR_PALMA_CREST = 3.5
INTERVALO_PALMAS = 1.0

VELOCIDADE_VOZ = 1.03
TONALIDADE_VOZ = 0.92
MAX_HISTORICO = 10

# Baixa Releases oficiais e atualiza o programa, incluindo sua interface.
# Defina False para pausar as atualizações automáticas.
MODO_MELHORIA_COMPLETA = True
