"""Monta o vídeo final: imagem estática com efeito Ken Burns (zoom lento) + áudio.

Usa ffmpeg diretamente (via subprocess), sem depender de bibliotecas Python
pesadas como moviepy.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import config
from .ffmpeg_util import get_ffmpeg_exe


class VideoBuildError(RuntimeError):
    """Erro ao montar o vídeo com ffmpeg."""


def get_audio_duration_seconds(audio_path: Path) -> float:
    """Retorna a duração do áudio em segundos usando mutagen (sem precisar de ffprobe)."""
    from mutagen import File as MutagenFile

    audio = MutagenFile(str(audio_path))
    if audio is None or audio.info is None:
        raise VideoBuildError(f"Não foi possível ler a duração de {audio_path}")
    return float(audio.info.length)


def build_video(
    image_path: Path,
    audio_path: Path,
    out_path: Path,
    duration: float | None = None,
    width: int = config.VIDEO_WIDTH,
    height: int = config.VIDEO_HEIGHT,
    fps: int = config.VIDEO_FPS,
) -> Path:
    """Renderiza o vídeo final em `out_path`. Retorna out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if duration is None:
        duration = get_audio_duration_seconds(audio_path)

    total_frames = max(int(duration * fps), fps)  # pelo menos 1s de vídeo
    upscale_w, upscale_h = width * 2, height * 2

    zoom_expr = f"min(zoom+{config.KEN_BURNS_SPEED},{config.KEN_BURNS_MAX_ZOOM})"
    filter_complex = (
        f"[0:v]scale={upscale_w}:{upscale_h}:force_original_aspect_ratio=increase,"
        f"crop={upscale_w}:{upscale_h},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
        f"format=yuv420p[v]"
    )

    ffmpeg = get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", config.VIDEO_BITRATE_AUDIO,
        "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoBuildError(
            f"ffmpeg falhou (código {result.returncode}):\n{result.stderr[-4000:]}"
        )
    return out_path
