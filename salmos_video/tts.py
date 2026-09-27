"""Geração de narração em áudio (Text-to-Speech), 100% gratuita.

Motor principal: edge-tts (vozes neurais do Microsoft Edge "Ler em voz alta"),
sem necessidade de chave de API. Fallback: gTTS (Google Translate TTS).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from . import config


class TTSError(RuntimeError):
    """Erro ao gerar a narração em áudio."""


async def _synthesize_edge_tts(text: str, out_path: Path, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=config.TTS_RATE,
        pitch=config.TTS_PITCH,
    )
    await communicate.save(str(out_path))


def _synthesize_gtts(text: str, out_path: Path) -> None:
    from gtts import gTTS

    tts = gTTS(text=text, lang="pt", slow=False)
    tts.save(str(out_path))


def synthesize_speech(
    text: str,
    out_path: Path,
    voice: str = config.TTS_VOICE,
    engine: str = config.TTS_ENGINE,
) -> Path:
    """Sintetiza `text` em áudio e salva em `out_path` (mp3). Retorna out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    errors = []

    if engine in ("edge-tts", "auto"):
        try:
            asyncio.run(_synthesize_edge_tts(text, out_path, voice))
            if out_path.exists() and out_path.stat().st_size > 0:
                return out_path
            errors.append("edge-tts gerou arquivo vazio")
        except Exception as exc:  # noqa: BLE001 - queremos cair no fallback
            errors.append(f"edge-tts falhou: {exc}")

    try:
        _synthesize_gtts(text, out_path)
        if out_path.exists() and out_path.stat().st_size > 0:
            return out_path
        errors.append("gTTS gerou arquivo vazio")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"gTTS falhou: {exc}")

    raise TTSError("Falha ao gerar narração: " + " | ".join(errors))
