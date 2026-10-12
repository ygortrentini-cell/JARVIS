from .procurar_programa import procurar
import subprocess
import os
import webbrowser
import shutil
import sys

PASTA_LOCAL = os.environ.get(
    "LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local")
)
PASTA_ROAMING = os.environ.get(
    "APPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
)

# ===============================
# PROGRAMAS INSTALADOS
# ===============================

PROGRAMAS = {

    # Navegadores
    "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",

    # Comunicação
    "whatsapp": "explorer.exe shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "discord": os.path.join(PASTA_LOCAL, "Discord", "Update.exe") + " --processStart Discord.exe",
    "telegram": os.path.join(PASTA_ROAMING, "Telegram Desktop", "Telegram.exe"),

    # Desenvolvimento
    "vs code": os.path.join(PASTA_LOCAL, "Programs", "Microsoft VS Code", "Code.exe"),
    "visual studio": r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
    "python": "python",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",

    # Jogos
    "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
    "minecraft": r"C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe",
    "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",

    # Windows
    "calculadora": "calc.exe",
    "bloco de notas": "notepad.exe",
    "paint": "mspaint.exe",
    "explorador": "explorer.exe",
    "gerenciador de tarefas": "taskmgr.exe",
    "painel de controle": "control.exe",
    "configurações": "ms-settings:",
    "câmera": "microsoft.windows.camera:",
    "gravador de voz": "ms-call-recording:",
    "teclado virtual": "osk.exe",

    # Office
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",

    # Multimídia
    "spotify": "spotify",
    "vlc": "vlc",
    "obs": "obs64.exe",

    # IA
    "ollama": "ollama",
}

# ===============================
# SITES
# ===============================

SITES = {

    "google": "https://google.com",

    "youtube": "https://youtube.com",

    "chatgpt": "https://chatgpt.com",

    "github": "https://github.com",

    "gmail": "https://mail.google.com",

    "instagram": "https://instagram.com",

    "facebook": "https://facebook.com",

    "x": "https://x.com",

    "twitter": "https://x.com",

    "linkedin": "https://linkedin.com",

    "netflix": "https://netflix.com",

    "prime video": "https://primevideo.com",

    "disney plus": "https://disneyplus.com",

    "max": "https://max.com",

    "twitch": "https://twitch.tv",

    "reddit": "https://reddit.com",

    "wikipedia": "https://wikipedia.org",

    "mercado livre": "https://mercadolivre.com.br",

    "amazon": "https://amazon.com.br",

    "ifood": "https://ifood.com.br",

    "google maps": "https://maps.google.com",

    "google tradutor": "https://translate.google.com",

    "google drive": "https://drive.google.com",

    "google agenda": "https://calendar.google.com",

    "google fotos": "https://photos.google.com",

    "speedtest": "https://speedtest.net",

    "pixlr": "https://pixlr.com",

    "canva": "https://canva.com",

    "figma": "https://figma.com"
}

# Nomes fixos de processos: o texto falado nunca é inserido no comando do shell.
PROCESSOS = {
    "brave": ("brave",),
    "chrome": ("chrome",),
    "google chrome": ("chrome",),
    "edge": ("msedge",),
    "microsoft edge": ("msedge",),
    "firefox": ("firefox",),
    "calculadora": ("Calculator", "CalculatorApp"),
    "bloco de notas": ("notepad",),
    "paint": ("mspaint",),
    "word": ("winword",),
    "excel": ("excel",),
    "powerpoint": ("powerpnt",),
    "spotify": ("Spotify",),
    "discord": ("Discord",),
    "telegram": ("Telegram",),
    "steam": ("steam",),
    "vlc": ("vlc",),
    "obs": ("obs64", "obs32"),
    "gerenciador de tarefas": ("Taskmgr",),
}


def _localizar_navegador(nome):
    """Procura o navegador solicitado sem redirecionar para outro browser."""
    executaveis = {
        "brave": ("brave.exe", "BraveSoftware/Brave-Browser/Application/brave.exe"),
        "chrome": ("chrome.exe", "Google/Chrome/Application/chrome.exe"),
        "edge": ("msedge.exe", "Microsoft/Edge/Application/msedge.exe"),
        "firefox": ("firefox.exe", "Mozilla Firefox/firefox.exe"),
    }
    executavel, caminho_relativo = executaveis[nome]
    candidatos = [PROGRAMAS[nome], shutil.which(executavel)]
    for raiz in (
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("LOCALAPPDATA"),
    ):
        if raiz:
            candidatos.append(os.path.join(raiz, caminho_relativo))
    for candidato in candidatos:
        if candidato and os.path.isfile(candidato):
            return candidato
    return None


def abrir_programa(nome, endereco=None):

    nome = nome.lower().strip()

    if nome in ("navegador", "browser"):
        return webbrowser.open(endereco or "https://www.google.com")

    if nome in ("brave", "chrome", "edge", "firefox"):
        caminho = _localizar_navegador(nome)
        if not caminho:
            return False
        try:
            argumentos = [caminho]
            if endereco:
                argumentos.append(endereco)
            subprocess.Popen(argumentos)
            return True
        except Exception as erro:
            print(erro)
            return False

    # Primeiro verifica se é um site
    if nome in SITES:

        webbrowser.open(SITES[nome])

        return True

    # Depois verifica programas
    if nome not in PROGRAMAS:

       return procurar(nome)

    caminho = PROGRAMAS[nome]

    try:

        if caminho.startswith("http"):

            webbrowser.open(caminho)

        elif caminho.startswith("explorer.exe shell"):

            subprocess.Popen(caminho, shell=True)

        elif caminho.endswith(":"):

            os.startfile(caminho)

        elif os.path.exists(caminho):

            subprocess.Popen(caminho)

        else:

            subprocess.Popen(caminho, shell=True)

        return True

    except Exception as erro:

        print(erro)

        return False


def fechar_programa(nome):
    """Solicita o fechamento normal de janelas de programas conhecidos."""
    nome = nome.lower().strip()
    processos = PROCESSOS.get(nome)
    if not processos:
        return f"Ainda não reconheço o programa {nome} para fechá-lo."

    if sys.platform != "win32":
        return "O fechamento de programas está disponível nesta versão para Windows."

    nomes_powershell = ",".join("'" + processo.replace("'", "''") + "'" for processo in processos)
    script = (
        f"$nomes = @({nomes_powershell}); "
        "$alvos = @(Get-Process -Name $nomes -ErrorAction SilentlyContinue); "
        "if ($alvos.Count -eq 0) { Write-Output 'nao_encontrado'; exit 0 }; "
        "$janelas = @($alvos | Where-Object { $_.MainWindowHandle -ne 0 }); "
        "if ($janelas.Count -eq 0) { Write-Output 'sem_janela'; exit 0 }; "
        "foreach ($janela in $janelas) { $null = $janela.CloseMainWindow() }; "
        "Start-Sleep -Milliseconds 900; "
        "$restantes = @(Get-Process -Name $nomes -ErrorAction SilentlyContinue | "
        "Where-Object { $_.MainWindowHandle -ne 0 }); "
        "if ($restantes.Count -eq 0) { Write-Output 'fechado' } "
        "else { Write-Output 'solicitado' }"
    )
    try:
        resultado = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return f"Não consegui solicitar o fechamento de {nome}."

    if resultado.returncode != 0:
        return f"O Windows não conseguiu fechar {nome}."
    estado = resultado.stdout.strip().splitlines()[-1].strip() if resultado.stdout.strip() else ""
    if estado == "nao_encontrado":
        return f"O {nome} não está aberto."
    if estado == "sem_janela":
        return f"Não encontrei uma janela aberta do {nome}."
    if estado == "fechado":
        return f"Fechei o {nome}."
    if estado == "solicitado":
        return f"Pedi ao {nome} para fechar. Ele pode estar aguardando salvar alguma alteração."
    return f"Não consegui confirmar se o {nome} fechou."
