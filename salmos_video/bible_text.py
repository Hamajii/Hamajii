"""Busca o texto de um Salmo em português usando a API gratuita bible-api.com."""
from __future__ import annotations

from dataclasses import dataclass

import requests

from . import config


class BibleTextError(RuntimeError):
    """Erro ao buscar o texto do salmo."""


@dataclass
class PsalmText:
    number: int
    reference: str
    verses: list[str]
    translation: str

    @property
    def full_text(self) -> str:
        return " ".join(self.verses)

    @property
    def title(self) -> str:
        return f"Salmo {self.number}"


def get_psalm_text(number: int, translation: str = config.DEFAULT_TRANSLATION) -> PsalmText:
    """Retorna o texto do salmo `number` na tradução dada.

    Tenta múltiplos formatos de referência porque a API aceita nomes de
    livro em inglês independentemente do idioma escolhido em `translation`.
    """
    last_error: Exception | None = None
    for template in config.BIBLE_REFERENCE_TEMPLATES:
        reference = template.format(n=number)
        url = f"{config.BIBLE_API_BASE}/{reference}"
        try:
            resp = requests.get(
                url, params={"translation": translation}, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            continue

        verses = [v["text"].strip() for v in data.get("verses", [])]
        if not verses:
            last_error = BibleTextError(f"Resposta sem versículos para '{reference}'")
            continue

        return PsalmText(
            number=number,
            reference=data.get("reference", reference),
            verses=verses,
            translation=translation,
        )

    raise BibleTextError(
        f"Não foi possível obter o Salmo {number} (tradução={translation}): {last_error}"
    )
