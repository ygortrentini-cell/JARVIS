import re
import unicodedata


CORRECOES_TRANSCRICAO = (
    (r"\bna\s+vegador\b", "navegador"),
    (r"\b(?:besquise|esquise|pesquize)\b", "pesquise"),
    (r"\bmastrite\b", "mostre"),
    (r"\bmimostri\b", "me mostre"),
    (r"\bfashion\s+a\s+vigador\b", "feche o navegador"),
)


def corrigir_transcricao(texto):
    """Corrige alguns enganos recorrentes do reconhecimento de voz em PT-BR."""
    texto = str(texto)
    for padrao, correcao in CORRECOES_TRANSCRICAO:
        def preservar_caixa(correspondencia):
            trecho = correspondencia.group(0)
            if trecho.isupper():
                return correcao.upper()
            if trecho[:1].isupper():
                return correcao.capitalize()
            return correcao

        texto = re.sub(padrao, preservar_caixa, texto, flags=re.IGNORECASE)
    return texto


def limpar_texto(texto):

    texto = re.sub(r"[*_#>`]", "", texto)

    texto = texto.replace("😊", "")

    texto = texto.replace("🤖", "")

    texto = texto.replace("🎉", "")

    texto = texto.replace("😀", "")

    return texto.strip()


def normalizar_comando(texto):
    """Normaliza texto reconhecido por voz para comparar intenções em PT-BR."""
    texto = unicodedata.normalize("NFKD", corrigir_transcricao(texto).lower())
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()
