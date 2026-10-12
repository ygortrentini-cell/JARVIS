# Voz Piper Cadu

O JARVIS prioriza `pt_BR-cadu-medium.onnx`, uma voz em português brasileiro com timbre mais grave. Se esse modelo não estiver disponível, tenta `pt_BR-faber-medium.onnx` e, por último, a voz masculina instalada no Windows. O modelo é carregado na primeira fala; a geração e reprodução seguintes ficam locais.

Para baixar os arquivos e instalar o mecanismo Piper no ambiente `.venv` do projeto, execute `powershell -ExecutionPolicy Bypass -File assets\voz\baixar_voz.ps1` na pasta JARVIS.

- Modelo e configuração: [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/pt/pt_BR/cadu/medium)
- Idioma: português brasileiro (`pt_BR`)
- Qualidade: medium; taxa de amostragem de 22.050 Hz
- Licença indicada pelo repositório: MIT; dados listados no cartão do modelo: CC0
- A síntese pode lembrar o estilo de um assistente de ficção científica, mas não é uma cópia da voz de Paul Bettany/JARVIS.
