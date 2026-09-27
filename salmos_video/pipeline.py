"""Orquestra a geração completa de um vídeo de Salmo, do texto ao mp4 final."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

from . import config
from .bible_text import get_psalm_text
from .tts import synthesize_speech
from .background_image import generate_background_image
from .thumbnail import build_thumbnail
from .video_builder import build_video, get_audio_duration_seconds

logger = logging.getLogger(__name__)

# Rotação de cenários visuais, para as imagens/thumbnails não ficarem
# todas idênticas quando se gera muitos vídeos em sequência.
VISUAL_THEMES = [
    "sunrise over green pastures and still waters",
    "vast desert at golden dusk with a single path",
    "calm sea under a dramatic sky at dawn",
    "ancient stone temple columns bathed in warm light",
    "misty mountains at sunrise with a shepherd's staff resting on a rock",
    "olive grove at sunset with soft warm light",
    "starry night sky over a quiet valley",
    "rolling green hills with a single old tree, soft morning light",
]


@dataclass
class PsalmVideoResult:
    number: int
    title: str
    reference: str
    audio_path: str
    background_path: str
    thumbnail_path: str
    video_path: str
    duration_seconds: float


def _visual_theme_for(number: int) -> str:
    return VISUAL_THEMES[number % len(VISUAL_THEMES)]


def process_psalm(
    number: int,
    output_dir: Path = config.OUTPUT_DIR,
    translation: str = config.DEFAULT_TRANSLATION,
    voice: str = config.TTS_VOICE,
) -> PsalmVideoResult:
    """Gera texto, áudio, imagem, thumbnail e vídeo final para um salmo."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / f"salmo_{number:03d}"

    logger.info("Salmo %s: buscando texto (%s)", number, translation)
    psalm = get_psalm_text(number, translation=translation)

    logger.info("Salmo %s: gerando narração", number)
    audio_path = synthesize_speech(psalm.full_text, prefix.with_suffix(".mp3"), voice=voice)
    duration = get_audio_duration_seconds(audio_path)

    logger.info("Salmo %s: gerando imagem de fundo", number)
    bg_path = generate_background_image(
        _visual_theme_for(number), prefix.with_name(prefix.name + "_bg.jpg")
    )

    logger.info("Salmo %s: montando thumbnail", number)
    thumb_path = build_thumbnail(
        bg_path,
        prefix.with_name(prefix.name + "_thumb.jpg"),
        main_text=psalm.title,
        sub_text="Palavra de Deus para hoje",
    )

    logger.info("Salmo %s: renderizando vídeo (%.1fs de áudio)", number, duration)
    video_path = build_video(
        bg_path, audio_path, prefix.with_suffix(".mp4"), duration=duration
    )

    return PsalmVideoResult(
        number=number,
        title=psalm.title,
        reference=psalm.reference,
        audio_path=str(audio_path),
        background_path=str(bg_path),
        thumbnail_path=str(thumb_path),
        video_path=str(video_path),
        duration_seconds=duration,
    )


def load_manifest(path: Path = config.MANIFEST_PATH) -> dict:
    if Path(path).exists():
        return json.loads(Path(path).read_text())
    return {}


def save_manifest(manifest: dict, path: Path = config.MANIFEST_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def record_result(result: PsalmVideoResult, path: Path = config.MANIFEST_PATH) -> None:
    manifest = load_manifest(path)
    manifest[str(result.number)] = asdict(result)
    save_manifest(manifest, path)
