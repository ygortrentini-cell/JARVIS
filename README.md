# J.A.R.V.I.S.

Assistente pessoal para Windows, com conversa por texto e voz, comandos locais e um painel inspirado nas interfaces holográficas de ficção científica.

## Iniciar

Dê dois cliques em `iniciar_jarvis.bat`. O iniciador usa o ambiente `.venv` da pasta quando ele existe; caso contrário, usa o Python disponível no Windows.

O painel também pode ser iniciado com `python main.py`.

Se as dependências ainda não estiverem instaladas, execute `python -m pip install -r requirements.txt` no ambiente Python usado pelo iniciador. Para a virtualenv desta pasta, use `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

Em uma instalação nova, copie `config.example.py` para `config.py` e ajuste o nome e o microfone. A configuração local, a memória, os registros, as gravações de teste e os modelos de voz ficam fora do pacote público de atualização.

## Recursos

- Conversa em português por texto ou microfone.
- Saudação falada ao iniciar com o estado atual de CPU, memória e armazenamento; o microfone só volta a escutar depois que ela termina.
- Captura de fala adaptada ao ruído ambiente, com mais margem para pausas e pedidos longos.
- Nova tentativa automática do Whisper em transcrições incertas e correção contextual de erros comuns de fala.
- Respostas com o Ollama e o modelo configurado em `config.py`.
- Leitura com a voz neural Piper Cadu em português do Brasil, de timbre mais grave, com cadência mais medida e execução local; se o modelo não estiver disponível, tenta a Piper Faber e depois a voz masculina do Windows.
- Comandos locais para abrir e fechar programas, pesquisar na web, consultar notícias recentes, calcular expressões e consultar recursos do computador.
- Manchetes atuais da Agência Brasil e publicações de pesquisa e inovação da EBC/NASA carregadas em segundo plano ao iniciar e atualizadas a cada 30 minutos; novas descobertas são sinalizadas na tela e pela área de notificações do Windows.
- Verificação de Releases do GitHub ao iniciar, a cada hora e quando você pedir “verificar atualizações”. Pacotes com hash SHA-256 válido são baixados em segundo plano e aplicados ao fechar o JARVIS; ele reabre com a versão nova.
- Depois de atualizar, o JARVIS anuncia por voz e na tela o que mudou e o conhecimento descrito nas notas da versão. Ele também guarda localmente as descobertas recentes dos feeds de pesquisa; pergunte “o que você aprendeu?” para ouvi-las junto com o resumo da atualização.
- Um briefing falado com as manchetes e o estado do computador nesses mesmos pedidos.
- O briefing usa manchetes públicas e telemetria local; não consulta banco, saldo ou webcam.
- Pesquisa visual por pedidos como “mostre imagens de Saturno” e “mostre vídeos sobre robótica”; imagens abrem no Google Imagens e vídeos no YouTube. Também aceita pedidos combinados como “me fale sobre Marte e mostre imagens”.
- Modo de programação com busca e leitura de código dentro da pasta do projeto JARVIS.
- Ações no computador e alterações no projeto são executadas sem caixa de confirmação quando fazem parte de um pedido claro.
- Memórias pessoais guardadas localmente em `dados/memoria.json`; diga, por exemplo, “lembre que gosto de café” e depois pergunte “o que você lembra de mim”. O JARVIS registra fatos pessoais quando você pede, mantém até 60 descobertas recentes dos feeds no computador e guarda o resumo de cada atualização.
- Respostas locais reconhecem variações comuns de acentuação e pontuação, e o comando “claro” pode concluir uma oferta anterior para consultar o sistema.
- Painel amplo inspirado na gravação: grade azul em perspectiva, núcleo holográfico animado com o estado “FALANDO”, manchete principal com imagem quando o feed fornece e três painéis menores de telemetria, notícias e descobertas; conversa em uma faixa compacta inferior, sem funções financeiras.

As ferramentas de programação leem e alteram arquivos de texto apenas dentro da pasta do projeto; pastas de ambiente, logs, dados pessoais e arquivos de credenciais ficam protegidos. Para pedidos explícitos envolvendo outros programas ou arquivos do Windows, o executor usa a conta atual do usuário. Ações no PC não exibem uma confirmação do JARVIS e só devem ocorrer em resposta a pedidos claros; o Windows ainda pode bloquear operações que exigem privilégios administrativos. O microfone encerra a gravação quando detecta uma pausa na fala, até o limite configurado. Se a IA produzir uma resposta inválida, tenta formulá-la novamente; se ainda não conseguir, pergunta se você quer uma explicação, uma pesquisa ou uma ação no computador. O modelo de IA é aquecido em segundo plano e mantido carregado durante a conversa. O botão pausa ou retoma a escuta. Se os módulos de áudio não estiverem disponíveis, a conversa por texto continua acessível.

## Organização

- `core/`: assistente, áudio, IA, memória e trabalhadores em segundo plano.
- `interface/`: janela e elementos visuais do painel.
- `modules/`: comandos, cálculos, programas, arquivos e consultas ao sistema.
- `assets/`: recursos visuais e sonoros.
- `dados/`: memória local do assistente.
- `logs/`: registros de execução.
- `tests/manual/`: utilitários manuais de áudio e voz.
- `docs/rascunhos/`: rascunhos preservados.

`main.py` é o ponto principal de inicialização. `jarvis.py` permanece como atalho compatível com inicializações antigas.

## Dependências

Instale os pacotes listados em `requirements.txt`. A voz Piper usa os arquivos em `assets/voz/`; o modelo Cadu é distribuído sob licença MIT e os dados de voz do cartão do modelo estão sob CC0. Para respostas de IA, o Ollama precisa estar instalado e em execução, com o modelo selecionado em `config.py` disponível localmente. O microfone requer os pacotes de áudio e um dispositivo de entrada válido em `AUDIO_DEVICE`.

## Publicar uma versão para o atualizador

O workflow `.github/workflows/release.yml` cria um pacote de atualização e seu hash SHA-256 quando uma tag `v*` é enviada ao GitHub. A versão da tag deve corresponder a `version.json` (por exemplo, `v0.3.0` e `0.3.0`); atualize também os campos `mudancas` e `aprendizados`, e crie `release-notes/vX.Y.Z.md` com as seções `O que mudou` e `O que aprendeu`. O pacote contém o código do assistente, mas preserva `config.py`, `.venv`, `dados/`, `logs/` e os modelos de voz locais. O JARVIS se atualiza por Releases publicadas nesse repositório; o modelo de IA não retreina nem reescreve o próprio código por conta própria.
