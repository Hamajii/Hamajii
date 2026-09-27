"""Geração gratuita de imagem de fundo via Pollinations.ai (sem chave de API).

Se a API estiver indisponível (rede bloqueada, timeout, etc.), cai para um
gradiente gerado localmente com PIL, para que o pipeline nunca trave.
"""
from __future__ import annotations

import logging
import random
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw

from . import config

logger = logging.getLogger(__name__)


def _build_prompt(theme_hint: str) -> str:
    return f"{theme_hint}, {config.IMAGE_STYLE_SUFFIX}"


def _download_pollinations_image(prompt: str, out_path: Path, width: int, height: int) -> None:
    encoded = quote(prompt)
    seed = random.randint(0, 999_999)
    url = f"{config.IMAGE_API_BASE}/{encoded}"
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "model": config.IMAGE_MODEL,
        "seed": seed,
    }
    resp = requests.get(url, params=params, timeout=90)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if "image" not in content_type:
        raise ValueError(f"Resposta inesperada (content-type={content_type})")
    out_path.write_bytes(resp.content)


def _fallback_gradient_image(out_path: Path, width: int, height: int) -> None:
    """Gera um gradiente suave localmente, sem depender de rede."""
    top = (30, 26, 60)
    bottom = (120, 90, 40)
    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    img.save(out_path, quality=92)


def generate_background_image(
    theme_hint: str,
    out_path: Path,
    width: int = config.IMAGE_WIDTH,
    height: int = config.IMAGE_HEIGHT,
) -> Path:
    """Gera (ou baixa) a imagem de fundo e salva em `out_path`. Retorna out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = _build_prompt(theme_hint)

    try:
        _download_pollinations_image(prompt, out_path, width, height)
        return out_path
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Falha ao gerar imagem via Pollinations.ai (%s). Usando gradiente local.",
            exc,
        )
        _fallback_gradient_image(out_path, width, height)
        return out_path
