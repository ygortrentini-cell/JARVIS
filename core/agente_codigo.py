"""Ferramentas para ler e alterar o projeto JARVIS a pedido do usuário."""

import os
import subprocess
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTAS_IGNORADAS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "dados",
    ".aws", ".codex", ".agents", ".env", ".ssh", "secrets",
}
EXTENSOES_TEXTO = {
    ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini",
    ".cfg", ".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".bat",
    ".ps1", ".xml", ".csv", ".sql", ".sh",
}


def _protegido(caminho):
    nome = caminho.name.casefold()
    return (
        nome == ".env"
        or nome.startswith(".env.")
        or any(palavra in nome for palavra in ("secret", "credential", "token", "password"))
        or caminho.suffix.casefold() in {".pem", ".pfx", ".p12", ".key"}
    )


def _caminho_projeto(caminho_relativo):
    informado = str(caminho_relativo or ".").strip()
    try:
        destino = (RAIZ_PROJETO / informado).resolve()
    except (OSError, RuntimeError):
        return None, "Esse caminho não pôde ser validado com segurança."
    try:
        destino.relative_to(RAIZ_PROJETO)
    except ValueError:
        return None, "Só posso acessar arquivos dentro da pasta do projeto JARVIS."

    partes = {parte.casefold() for parte in destino.relative_to(RAIZ_PROJETO).parts}
    if partes.intersection(PASTAS_IGNORADAS):
        return None, "Essa pasta está protegida contra leitura ou alteração pelo agente."
    if _protegido(destino):
        return None, "Esse tipo de arquivo contém dados sensíveis e não será acessado."
    return destino, None


def _iterar_arquivos(pasta):
    if pasta.is_file():
        if pasta.suffix.casefold() in EXTENSOES_TEXTO and not _protegido(pasta):
            yield pasta
        return

    for atual, diretorios, nomes in os.walk(pasta):
        diretorios[:] = [
            nome for nome in diretorios
            if nome.casefold() not in PASTAS_IGNORADAS
        ]
        for nome in nomes:
            arquivo = Path(atual) / nome
            if (
                not arquivo.is_symlink()
                and arquivo.suffix.casefold() in EXTENSOES_TEXTO
                and not _protegido(arquivo)
            ):
                yield arquivo


def listar_arquivos(caminho="."):
    pasta, erro = _caminho_projeto(caminho)
    if erro:
        return erro
    if not pasta.exists():
        return f"Não encontrei {caminho} dentro do projeto."
    if pasta.is_file():
        return str(pasta.relative_to(RAIZ_PROJETO))

    itens = []
    for arquivo in _iterar_arquivos(pasta):
        itens.append(str(arquivo.relative_to(RAIZ_PROJETO)))
        if len(itens) >= 200:
            itens.append("Lista limitada aos primeiros 200 arquivos.")
            break
    return "\n".join(itens) if itens else "Não encontrei arquivos de texto nessa pasta."


def buscar_texto(termo, caminho="."):
    termo = str(termo or "").strip()
    if not termo:
        return "Informe o texto que devo procurar."
    if len(termo) > 300:
        return "O texto de busca é longo demais."

    pasta, erro = _caminho_projeto(caminho)
    if erro:
        return erro
    if not pasta.exists():
        return f"Não encontrei {caminho} dentro do projeto."

    resultados = []
    alvo = termo.casefold()
    for arquivo in _iterar_arquivos(pasta):
        try:
            if arquivo.stat().st_size > 500_000:
                continue
            linhas = arquivo.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for numero, linha in enumerate(linhas, start=1):
            if alvo in linha.casefold():
                trecho = linha.strip()[:240]
                resultados.append(
                    f"{arquivo.relative_to(RAIZ_PROJETO)}:{numero}: {trecho}"
                )
                if len(resultados) >= 40:
                    resultados.append("Busca limitada aos primeiros 40 resultados.")
                    return "\n".join(resultados)
    return "\n".join(resultados) if resultados else "Não encontrei esse texto no projeto."


def ler_arquivo(caminho):
    arquivo, erro = _caminho_projeto(caminho)
    if erro:
        return erro
    if not arquivo.is_file():
        return f"Não encontrei o arquivo {caminho}."
    if arquivo.suffix.casefold() not in EXTENSOES_TEXTO:
        return "Só posso ler arquivos de texto e código."
    try:
        if arquivo.stat().st_size > 500_000:
            return "O arquivo é grande demais para abrir de uma vez."
        linhas = arquivo.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as erro_leitura:
        return f"Não consegui ler o arquivo: {erro_leitura}"

    conteudo = "\n".join(f"{n:4}: {linha}" for n, linha in enumerate(linhas, 1))
    return conteudo[:24_000] or "O arquivo está vazio."


def gravar_arquivo(caminho, conteudo, confirmacao, motivo=""):
    arquivo, erro = _caminho_projeto(caminho)
    if erro:
        return erro
    if arquivo.suffix.casefold() not in EXTENSOES_TEXTO:
        return "Só posso criar ou alterar arquivos de texto e código."
    if not isinstance(conteudo, str):
        return "O conteúdo precisa ser texto."
    if len(conteudo) > 100_000:
        return "A alteração é grande demais para uma única operação. Divida em partes menores."
    if arquivo.exists() and not arquivo.is_file():
        return "O destino existe, mas não é um arquivo."

    try:
        anterior = arquivo.read_text(encoding="utf-8") if arquivo.exists() else ""
    except (OSError, UnicodeError) as erro_leitura:
        return f"Não consegui preparar a alteração: {erro_leitura}"
    if anterior == conteudo:
        return "O arquivo já contém esse conteúdo; nenhuma alteração foi feita."

    if confirmacao is None or not confirmacao.pedir(
        "Alteração no projeto",
        str(motivo or "").strip() or f"O JARVIS quer gravar {arquivo.relative_to(RAIZ_PROJETO)}.",
        f"Arquivo solicitado: {arquivo.relative_to(RAIZ_PROJETO)}",
    ):
        return "Alteração cancelada; o arquivo não foi modificado."

    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(conteudo, encoding="utf-8", newline="")
    except OSError as erro_escrita:
        return f"Não consegui gravar o arquivo: {erro_escrita}"
    return f"Alteração gravada em {arquivo.relative_to(RAIZ_PROJETO)}."


def executar_comando(comando, confirmacao, motivo=""):
    comando = str(comando or "").strip()
    if not comando:
        return "Informe o comando que devo executar."
    if len(comando) > 2_000:
        return "O comando é longo demais para ser executado pelo agente."
    if confirmacao is None or not confirmacao.pedir(
        "Comando do projeto",
        str(motivo or "").strip() or "O JARVIS quer executar este comando no PowerShell.",
        f"Pasta de trabalho: {RAIZ_PROJETO}\n\n{comando}",
    ):
        return "Comando cancelado; nada foi executado."

    try:
        resultado = subprocess.run(
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; " + comando,
            ],
            cwd=str(RAIZ_PROJETO),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return "O comando passou do limite de dois minutos e foi interrompido."
    except OSError as erro_execucao:
        return f"Não consegui iniciar o comando: {erro_execucao}"

    saidas = [parte.strip() for parte in (resultado.stdout, resultado.stderr) if parte.strip()]
    saida = "\n".join(saidas)[:8_000]
    if resultado.returncode:
        return f"O comando terminou com erro ({resultado.returncode}):\n{saida}"
    return saida or "O comando foi concluído sem imprimir resultado."
