import os
import subprocess


def executar_arquivo(comando):

    comando = comando.lower()

    # ===========================
    # CRIAR PASTA
    # ===========================

    if "crie uma pasta chamada" in comando:

        nome = comando.replace("crie uma pasta chamada", "").strip()

        os.makedirs(nome, exist_ok=True)

        return f"Pasta {nome} criada."

    # ===========================
    # CRIAR ARQUIVO
    # ===========================

    if "crie um arquivo chamado" in comando:

        nome = comando.replace("crie um arquivo chamado", "").strip()

        open(nome, "a", encoding="utf-8").close()

        return f"Arquivo {nome} criado."

    # ===========================
    # ABRIR DOWNLOADS
    # ===========================

    if "downloads" in comando:

        subprocess.Popen("explorer shell:Downloads")

        return "Abrindo Downloads."

    # ===========================
    # ABRIR DOCUMENTOS
    # ===========================

    if "documentos" in comando:

        subprocess.Popen("explorer shell:Personal")

        return "Abrindo Documentos."

    # ===========================
    # ABRIR ÁREA DE TRABALHO
    # ===========================

    if "área de trabalho" in comando or "desktop" in comando:

        subprocess.Popen(
            f'explorer "{os.path.join(os.environ["USERPROFILE"], "Desktop")}"'
        )

        return "Abrindo a área de trabalho."

    return None