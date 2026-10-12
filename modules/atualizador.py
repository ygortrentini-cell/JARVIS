"""Verifica Releases do GitHub e aplica pacotes JARVIS validados ao encerrar."""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile


RAIZ = Path(__file__).resolve().parents[1]
PASTA_ATUALIZACOES = RAIZ / ".updates"
ARQUIVO_VERSAO = RAIZ / "version.json"
REPO = "ygortrentini-cell/JARVIS"
API_RELEASE = f"https://api.github.com/repos/{REPO}/releases/latest"
NOME_PACOTE = "JARVIS-update.zip"
NOME_HASH = f"{NOME_PACOTE}.sha256"
TAMANHO_MAXIMO_PACOTE = 100 * 1024 * 1024
TAMANHO_MAXIMO_EXTRAIDO = 250 * 1024 * 1024
LIMITE_ARQUIVOS = 3000

ARQUIVOS_RAIZ_PERMITIDOS = {
    "main.py",
    "jarvis.py",
    "iniciar_jarvis.bat",
    "requirements.txt",
    "README.md",
    "version.json",
    "config.example.py",
}
PASTAS_CODIGO_PERMITIDAS = {"core", "modules", "interface"}


def ler_versao_local():
    try:
        dados = json.loads(ARQUIVO_VERSAO.read_text(encoding="utf-8"))
        return str(dados.get("version", "0.0.0"))
    except (OSError, ValueError, TypeError):
        return "0.0.0"


def _chave_versao(texto):
    correspondencia = re.fullmatch(r"[vV]?(\d+(?:\.\d+)*)", str(texto).strip())
    if not correspondencia:
        return None
    return tuple(int(parte) for parte in correspondencia.group(1).split("."))


def _versao_maior(a, b):
    chave_a = _chave_versao(a)
    chave_b = _chave_versao(b)
    if chave_a is None or chave_b is None:
        return False
    tamanho = max(len(chave_a), len(chave_b))
    return chave_a + (0,) * (tamanho - len(chave_a)) > chave_b + (0,) * (tamanho - len(chave_b))


def _baixar(url, limite, binario=False):
    cabecalhos = {
        "User-Agent": "JARVIS-Updater/1.0",
        "Accept": "application/octet-stream" if binario else "application/vnd.github+json",
    }
    pedido = urllib.request.Request(url, headers=cabecalhos)
    with urllib.request.urlopen(pedido, timeout=15) as resposta:
        dados = resposta.read(limite + 1)
    if len(dados) > limite:
        raise ValueError("O arquivo remoto excede o limite permitido.")
    return dados


def _permitido(nome, eh_pasta=False):
    caminho = PurePosixPath(nome)
    if caminho.is_absolute() or not caminho.parts or ".." in caminho.parts:
        return False
    if len(caminho.parts) == 1:
        return eh_pasta or nome in ARQUIVOS_RAIZ_PERMITIDOS
    if caminho.parts[0] in PASTAS_CODIGO_PERMITIDAS:
        return eh_pasta or caminho.suffix.lower() == ".py"
    return False


def _validar_pacote(dados, versao_release):
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as pacote:
            membros = pacote.infolist()
            if not membros or len(membros) > LIMITE_ARQUIVOS:
                return False

            nomes = set()
            total_extraido = 0
            for membro in membros:
                nome_original = membro.filename.replace("\\", "/")
                if nome_original.startswith("/"):
                    return False
                nome = nome_original.rstrip("/")
                if not nome or nome in nomes or not _permitido(nome, membro.is_dir()):
                    return False
                nomes.add(nome)
                modo = (membro.external_attr >> 16) & 0o170000
                if modo == stat.S_IFLNK:
                    return False
                total_extraido += membro.file_size
                if total_extraido > TAMANHO_MAXIMO_EXTRAIDO:
                    return False

            dados_versao = pacote.read("version.json")
            versao_pacote = str(json.loads(dados_versao.decode("utf-8")).get("version", ""))
            if versao_pacote != versao_release:
                return False
            return pacote.testzip() is None
    except (OSError, ValueError, KeyError, UnicodeDecodeError, zipfile.BadZipFile):
        return False


def _notas_curta(texto, limite=220):
    texto = re.sub(r"<[^>]*>", " ", str(texto or ""))
    texto = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", texto)
    texto = re.sub(r"[`*_#]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()[:limite]


def _resumir_notas_release(texto):
    secoes = {"mudancas": [], "aprendizados": []}
    secao_atual = None
    for linha in str(texto or "").splitlines():
        cabecalho = re.match(r"^\s{0,3}#{1,6}\s*(.+?)\s*#*\s*$", linha)
        if cabecalho:
            titulo = unicodedata.normalize("NFKD", cabecalho.group(1).casefold())
            titulo = "".join(caractere for caractere in titulo if not unicodedata.combining(caractere))
            if any(palavra in titulo for palavra in ("mudou", "mudancas", "novidades", "changes")):
                secao_atual = "mudancas"
            elif any(palavra in titulo for palavra in ("aprendeu", "aprendizados", "conhecimento", "learned")):
                secao_atual = "aprendizados"
            else:
                secao_atual = None
            continue
        if secao_atual:
            item = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", linha).strip()
            if item:
                secoes[secao_atual].append(item)

    mudancas = _notas_curta("; ".join(secoes["mudancas"]), 200)
    aprendizados = _notas_curta("; ".join(secoes["aprendizados"]), 200)
    if not mudancas:
        mudancas = _notas_curta(texto, 200) or "Melhorias e correções desta versão."
    if not aprendizados:
        aprendizados = "Esta versão não especificou novos conhecimentos nas notas."
    return mudancas, aprendizados


class Atualizador:
    def __init__(self):
        self.pacote_preparado = None
        self.mudancas_preparadas = ""
        self.aprendizados_preparados = ""

    def verificar_e_preparar(self):
        atual = ler_versao_local()
        try:
            try:
                release = json.loads(_baixar(API_RELEASE, 1_000_000).decode("utf-8"))
            except urllib.error.HTTPError as erro:
                if erro.code == 404:
                    return {"status": "sem_release", "atual": atual}
                raise

            tag = str(release.get("tag_name", "")).strip()
            versao = tag.lstrip("vV")
            if not _versao_maior(versao, atual):
                return {"status": "atualizado", "atual": atual}
            mudancas, aprendizados = _resumir_notas_release(release.get("body"))

            ativos = {item.get("name"): item for item in release.get("assets", [])}
            pacote = ativos.get(NOME_PACOTE)
            checksum = ativos.get(NOME_HASH)
            if not pacote or not checksum:
                return {
                    "status": "release_incompleta",
                    "atual": atual,
                    "versao": tag,
                    "notas": _notas_curta(release.get("body")),
                    "mudancas": mudancas,
                    "aprendizados": aprendizados,
                }
            tamanho = int(pacote.get("size", 0) or 0)
            if tamanho < 1 or tamanho > TAMANHO_MAXIMO_PACOTE:
                raise ValueError("O pacote publicado tem um tamanho inválido.")

            dados_pacote = _baixar(pacote["browser_download_url"], TAMANHO_MAXIMO_PACOTE, True)
            dados_hash = _baixar(checksum["browser_download_url"], 4096, True).decode("ascii", "ignore")
            correspondencia = re.search(r"\b([a-fA-F0-9]{64})\b", dados_hash)
            if not correspondencia:
                raise ValueError("A Release não publicou um hash SHA-256 válido.")
            hash_esperado = correspondencia.group(1).lower()
            hash_calculado = hashlib.sha256(dados_pacote).hexdigest()
            if hash_esperado != hash_calculado:
                raise ValueError("O hash SHA-256 do pacote não confere.")
            if not _validar_pacote(dados_pacote, versao):
                raise ValueError("O pacote não passou pela validação de arquivos e versão.")

            PASTA_ATUALIZACOES.mkdir(parents=True, exist_ok=True)
            arquivo = PASTA_ATUALIZACOES / f"JARVIS-update-{versao}.zip"
            arquivo.write_bytes(dados_pacote)
            self.pacote_preparado = arquivo
            self.mudancas_preparadas = mudancas
            self.aprendizados_preparados = aprendizados
            return {
                "status": "pronta",
                "atual": atual,
                "versao": tag,
                "arquivo": str(arquivo),
                "notas": _notas_curta(release.get("body")),
                "mudancas": mudancas,
                "aprendizados": aprendizados,
            }
        except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as erro:
            return {"status": "erro", "atual": atual, "detalhe": str(erro)[:180]}

    def agendar_aplicacao(self, processo_pai):
        arquivo = self.pacote_preparado
        if not arquivo or not Path(arquivo).is_file():
            return False

        interpretador = Path(sys.executable)
        pythonw = interpretador.with_name("pythonw.exe")
        if os.name == "nt" and pythonw.is_file():
            interpretador = pythonw
        entrada = Path(sys.argv[0])
        if not entrada.is_absolute():
            entrada = (Path.cwd() / entrada).resolve()
        if not entrada.is_file():
            entrada = RAIZ / "main.py"

        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        try:
            subprocess.Popen(
                [
                    str(interpretador),
                    str(Path(__file__).resolve()),
                    "--aplicar",
                    str(Path(arquivo).resolve()),
                    "--aguardar-pid",
                    str(int(processo_pai)),
                    "--python",
                    str(Path(sys.executable).resolve()),
                    "--entrada",
                    str(entrada),
                    "--mudancas",
                    self.mudancas_preparadas,
                    "--aprendizados",
                    self.aprendizados_preparados,
                ],
                cwd=str(RAIZ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=flags,
            )
            return True
        except OSError as erro:
            _registrar(f"Não foi possível iniciar o aplicador: {erro}")
            return False


def _registrar(mensagem):
    try:
        PASTA_ATUALIZACOES.mkdir(parents=True, exist_ok=True)
        with (PASTA_ATUALIZACOES / "atualizador.log").open("a", encoding="utf-8") as arquivo:
            arquivo.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {mensagem}\n")
    except OSError:
        pass


def _configuracao_literal(caminho):
    valores = {}
    try:
        arvore = ast.parse(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return valores
    for no in arvore.body:
        if isinstance(no, ast.Assign) and len(no.targets) == 1 and isinstance(no.targets[0], ast.Name):
            nome = no.targets[0].id
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            nome = no.target.id
        else:
            continue
        try:
            valores[nome] = ast.literal_eval(no.value)
        except (ValueError, TypeError):
            continue
    return valores


def _mesclar_novas_opcoes_configuracao(caminho_local, caminho_modelo):
    caminho_local = Path(caminho_local)
    caminho_modelo = Path(caminho_modelo)
    if not caminho_modelo.is_file():
        return False
    if not caminho_local.exists():
        caminho_local.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(caminho_modelo, caminho_local)
        return True

    valores_modelo = _configuracao_literal(caminho_modelo)
    valores_locais = _configuracao_literal(caminho_local)
    novos = [(nome, valor) for nome, valor in valores_modelo.items() if nome not in valores_locais]
    if not novos:
        return False

    with caminho_local.open("a", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("\n\n# Opções adicionadas pela atualização do JARVIS; ajuste se desejar.\n")
        for nome, valor in novos:
            arquivo.write(f"{nome} = {valor!r}\n")
    return True


def _processo_ativo(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        processo = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not processo:
            return ctypes.get_last_error() == 5  # access denied: aguarde por segurança
        try:
            codigo = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(processo, ctypes.byref(codigo)):
                return True
            return codigo.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(processo)

    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _salvar_resumo_atualizacao(versao, mudancas, aprendizados):
    pasta_dados = RAIZ / "dados"
    destino = pasta_dados / "ultima_atualizacao.json"
    temporario = destino.with_suffix(".json.tmp")
    registro = {
        "versao": str(versao),
        "mudancas": _notas_curta(mudancas, 200),
        "aprendizados": _notas_curta(aprendizados, 200),
        "instalada_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        "anunciada": False,
    }
    if not registro["aprendizados"]:
        registro["aprendizados"] = "Esta versão não especificou novos conhecimentos nas notas."
    try:
        pasta_dados.mkdir(parents=True, exist_ok=True)
        temporario.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        temporario.replace(destino)
    except OSError as erro:
        _registrar(f"Não foi possível salvar o resumo da atualização: {erro}")


def _aplicar_pacote(arquivo_zip, pid, interpretador, entrada, mudancas="", aprendizados=""):
    arquivo = Path(arquivo_zip).resolve()
    pasta_atualizacoes = PASTA_ATUALIZACOES.resolve()
    if not arquivo.is_relative_to(pasta_atualizacoes) or not arquivo.name.startswith("JARVIS-update-"):
        _registrar("Pacote fora da pasta de atualizações; aplicação recusada.")
        return 1

    limite_espera = time.monotonic() + 300
    while _processo_ativo(pid) and time.monotonic() < limite_espera:
        time.sleep(0.5)
    if _processo_ativo(pid):
        _registrar("O JARVIS continuou aberto; a atualização foi cancelada.")
        return 1

    try:
        dados = arquivo.read_bytes()
        with zipfile.ZipFile(io.BytesIO(dados)) as pacote:
            versao = str(json.loads(pacote.read("version.json").decode("utf-8")).get("version", ""))
            if not _validar_pacote(dados, versao):
                raise ValueError("O pacote mudou depois da validação.")

            pasta_stage = PASTA_ATUALIZACOES / f"stage-{versao}"
            pasta_backup = PASTA_ATUALIZACOES / f"backup-{versao}"
            pasta_stage.mkdir(parents=True, exist_ok=True)
            pasta_backup.mkdir(parents=True, exist_ok=True)

            nomes = []
            for membro in pacote.infolist():
                nome = membro.filename.replace("\\", "/").strip("/")
                if membro.is_dir():
                    continue
                destino_stage = pasta_stage.joinpath(*PurePosixPath(nome).parts)
                destino_stage.parent.mkdir(parents=True, exist_ok=True)
                with pacote.open(membro, "r") as origem, destino_stage.open("wb") as destino:
                    shutil.copyfileobj(origem, destino)
                nomes.append(nome)

        arquivo_requisitos_novos = pasta_stage / "requirements.txt"
        arquivo_requisitos_atual = RAIZ / "requirements.txt"
        if (
            arquivo_requisitos_novos.is_file()
            and arquivo_requisitos_atual.is_file()
            and arquivo_requisitos_novos.read_bytes() != arquivo_requisitos_atual.read_bytes()
        ):
            instalacao = subprocess.run(
                [interpretador, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(arquivo_requisitos_novos)],
                cwd=str(RAIZ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=900,
                check=False,
                creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0),
            )
            if instalacao.returncode != 0:
                raise RuntimeError("Não foi possível instalar as dependências da nova versão.")

        alterados = []
        criados = []
        try:
            for nome in nomes:
                caminho = PurePosixPath(nome)
                origem = pasta_stage.joinpath(*caminho.parts)
                destino = RAIZ.joinpath(*caminho.parts)
                if not destino.resolve().is_relative_to(RAIZ.resolve()):
                    raise ValueError("Um caminho do pacote saiu da pasta do JARVIS.")
                destino.parent.mkdir(parents=True, exist_ok=True)
                if destino.exists():
                    copia = pasta_backup.joinpath(*caminho.parts)
                    copia.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(destino, copia)
                    alterados.append((destino, copia))
                else:
                    criados.append(destino)
                shutil.copy2(origem, destino)

            arquivo_config_local = RAIZ / "config.py"
            arquivo_config_modelo = pasta_stage / "config.example.py"
            if arquivo_config_modelo.is_file():
                backup_config = pasta_backup / "config.py"
                if arquivo_config_local.exists():
                    backup_config.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(arquivo_config_local, backup_config)
                    alterados.append((arquivo_config_local, backup_config))
                else:
                    criados.append(arquivo_config_local)
                _mesclar_novas_opcoes_configuracao(arquivo_config_local, arquivo_config_modelo)
        except Exception:
            for destino, copia in reversed(alterados):
                shutil.copy2(copia, destino)
            for destino in criados:
                try:
                    destino.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

        for pasta in ("core", "modules", "interface"):
            for cache in (RAIZ / pasta).rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)

        _salvar_resumo_atualizacao(versao, mudancas, aprendizados)
        _registrar(f"Atualização {versao} aplicada. Reiniciando o JARVIS.")
        interpretador_reinicio = Path(interpretador)
        pythonw = interpretador_reinicio.with_name("pythonw.exe")
        if os.name == "nt" and pythonw.is_file():
            interpretador_reinicio = pythonw
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        subprocess.Popen(
            [str(interpretador_reinicio), str(entrada)],
            cwd=str(RAIZ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=flags,
        )
        return 0
    except Exception as erro:
        _registrar(f"Falha ao aplicar a atualização: {erro}")
        return 1


def _cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", required=True)
    parser.add_argument("--aguardar-pid", required=True, type=int)
    parser.add_argument("--python", required=True)
    parser.add_argument("--entrada", required=True)
    parser.add_argument("--mudancas", default="")
    parser.add_argument("--aprendizados", default="")
    argumentos = parser.parse_args()
    raise SystemExit(
        _aplicar_pacote(
            argumentos.aplicar,
            argumentos.aguardar_pid,
            argumentos.python,
            argumentos.entrada,
            argumentos.mudancas,
            argumentos.aprendizados,
        )
    )


if __name__ == "__main__":
    _cli()
