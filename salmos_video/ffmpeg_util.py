"""Localiza um executável ffmpeg utilizável.

Usa o ffmpeg do sistema se estiver no PATH; caso contrário, baixa/usa o
binário estático empacotado pelo pacote `imageio-ffmpeg` (instalado via pip),
o que evita depender do gerenciador de pacotes do sistema operacional.
"""
from __future__ import annotations

import shutil


def get_ffmpeg_exe() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()
