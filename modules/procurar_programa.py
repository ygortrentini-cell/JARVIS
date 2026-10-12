import os
import subprocess

PASTAS = [

    os.path.join(os.environ["ProgramData"],
                 r"Microsoft\Windows\Start Menu\Programs"),

    os.path.join(os.environ["APPDATA"],
                 r"Microsoft\Windows\Start Menu\Programs"),

    os.path.join(os.environ["USERPROFILE"],
                 "Desktop")
]


def procurar(nome):

    nome = nome.lower()

    for pasta in PASTAS:

        for raiz, _, arquivos in os.walk(pasta):

            for arquivo in arquivos:

                if arquivo.lower().startswith(nome):

                    caminho = os.path.join(raiz, arquivo)

                    try:

                        os.startfile(caminho)

                        return True

                    except:

                        pass

    return False