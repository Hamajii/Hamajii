"""Geração de thumbnail chamativa para o YouTube, usando Pillow."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

from . import config


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in config.FONT_CANDIDATES_BOLD:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def _fit_cover(img: Image.Image, width: int, height: int) -> Image.Image:
    return ImageOps.fit(img, (width, height), method=Image.LANCZOS)


def build_thumbnail(
    background_path: Path,
    out_path: Path,
    main_text: str,
    sub_text: str = "",
    width: int = config.THUMB_WIDTH,
    height: int = config.THUMB_HEIGHT,
) -> Path:
    """Cria a thumbnail em `out_path` a partir da imagem de fundo. Retorna out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base = Image.open(background_path).convert("RGB")
    base = _fit_cover(base, width, height)

    # Escurece levemente e aplica um leve desfoque para dar profundidade.
    base = base.filter(ImageFilter.GaussianBlur(1))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Gradiente escuro na base para o texto ficar legível.
    gradient_height = int(height * 0.55)
    for y in range(gradient_height):
        alpha = int(200 * (y / gradient_height))
        draw.line(
            [(0, height - gradient_height + y), (width, height - gradient_height + y)],
            fill=(0, 0, 0, alpha),
        )
    # Faixa escura leve no topo, para eventuais textos superiores.
    draw.rectangle([0, 0, width, int(height * 0.12)], fill=(0, 0, 0, 80))

    composed = Image.alpha_composite(base.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(composed)
    main_font = _load_font(size=int(height * 0.16))
    sub_font = _load_font(size=int(height * 0.06))

    margin = int(width * 0.05)
    main_y = height - int(height * 0.30)
    _draw_text_with_shadow(
        draw, (margin, main_y), main_text, main_font, fill=(255, 215, 120, 255)
    )

    if sub_text:
        sub_y = main_y + int(height * 0.17)
        _draw_text_with_shadow(
            draw, (margin, sub_y), sub_text, sub_font, fill=(255, 255, 255, 235)
        )

    composed.convert("RGB").save(out_path, quality=95)
    return out_path


def _draw_text_with_shadow(draw: ImageDraw.ImageDraw, pos, text, font, fill):
    x, y = pos
    shadow_offset = max(2, font.size // 20)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=fill)
