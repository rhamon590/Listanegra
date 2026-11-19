"""Contagens do fichário por unidade federativa e região."""

import json
import unicodedata
from collections import Counter
from pathlib import Path


REGIOES = {
    "1": "Norte",
    "2": "Nordeste",
    "3": "Sudeste",
    "4": "Sul",
    "5": "Centro-Oeste",
}

# Geometria simplificada de Click That 'Hood, distribuída com a aplicação.
UFS = json.loads(
    (Path(__file__).resolve().parent / "static" / "brasil-ufs.json").read_text(encoding="utf-8")
)


def normalizar_estado(valor):
    texto = unicodedata.normalize("NFKD", valor or "")
    sem_acentos = "".join(char for char in texto if not unicodedata.combining(char))
    return " ".join(sem_acentos.upper().split())


SIGLAS_POR_NOME = {
    normalizar_estado(dados["name"]): uf for uf, dados in UFS.items()
}


def resumir_estados(grupos):
    contagens = Counter()
    sem_uf = 0
    for estado, quantidade in grupos:
        chave = normalizar_estado(estado)
        uf = chave if chave in UFS else SIGLAS_POR_NOME.get(chave)
        if uf:
            contagens[uf] += quantidade
        else:
            sem_uf += quantidade
    return contagens, sem_uf
