import re


def calcular(comando):

    comando = comando.lower()

    comando = comando.replace("quanto é", "")
    comando = comando.replace("calcule", "")

    comando = comando.replace("mais", "+")
    comando = comando.replace("menos", "-")
    comando = comando.replace("vezes", "*")
    comando = comando.replace("x", "*")
    comando = comando.replace("multiplicado por", "*")
    comando = comando.replace("dividido por", "/")

    comando = comando.strip()

    # Só permite números e operadores
    if not re.fullmatch(r"[0-9+\-*/(). ]+", comando):
        return None

    try:
        resultado = eval(comando, {"__builtins__": {}}, {})
        return f"O resultado é {resultado}."

    except:
        return None