"""CLI para gerar (e opcionalmente subir) vídeos de Salmos em massa.

Exemplos:
    python -m salmos_video.cli --psalms 1,23,91
    python -m salmos_video.cli --range 1-10 --output-dir output/lote1
    python -m salmos_video.cli --psalms 23 --upload --privacy unlisted
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import config
from .pipeline import process_psalm, record_result, load_manifest


def _parse_psalm_list(psalms_arg: str | None, range_arg: str | None) -> list[int]:
    numbers: set[int] = set()
    if psalms_arg:
        for part in psalms_arg.split(","):
            part = part.strip()
            if part:
                numbers.add(int(part))
    if range_arg:
        start, end = range_arg.split("-")
        numbers.update(range(int(start), int(end) + 1))
    if not numbers:
        raise SystemExit("Informe --psalms e/ou --range.")
    for n in numbers:
        if not (1 <= n <= 150):
            raise SystemExit(f"Número de salmo inválido: {n} (deve estar entre 1 e 150)")
    return sorted(numbers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gerador em massa de vídeos de Salmos")
    parser.add_argument("--psalms", help="Lista separada por vírgula, ex: 1,23,91")
    parser.add_argument("--range", help="Faixa, ex: 1-10")
    parser.add_argument("--output-dir", default=str(config.OUTPUT_DIR))
    parser.add_argument("--translation", default=config.DEFAULT_TRANSLATION)
    parser.add_argument("--voice", default=config.TTS_VOICE)
    parser.add_argument("--skip-existing", action="store_true", default=True,
                         help="Pula salmos já presentes no manifest (padrão)")
    parser.add_argument("--force", action="store_true",
                         help="Regenera mesmo que já exista no manifest")
    parser.add_argument("--upload", action="store_true", help="Envia os vídeos gerados ao YouTube")
    parser.add_argument("--privacy", default=config.YOUTUBE_DEFAULT_PRIVACY,
                         choices=["private", "unlisted", "public"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output_dir = Path(args.output_dir)
    numbers = _parse_psalm_list(args.psalms, args.range)
    manifest = load_manifest()

    to_upload = []
    successes, failures = [], []

    for number in numbers:
        if not args.force and str(number) in manifest:
            logging.info("Salmo %s já processado anteriormente, pulando (use --force para refazer).", number)
            continue
        try:
            result = process_psalm(
                number,
                output_dir=output_dir,
                translation=args.translation,
                voice=args.voice,
            )
            record_result(result)
            successes.append(result)
            if args.upload:
                to_upload.append({
                    "video_path": Path(result.video_path),
                    "title": f"{result.title} - Palavra de Deus para hoje",
                    "description": (
                        f"{result.title} ({result.reference})\n\n"
                        "Vídeo devocional gerado automaticamente. "
                        "#salmos #biblia #fe"
                    ),
                    "thumbnail_path": Path(result.thumbnail_path),
                    "privacy_status": args.privacy,
                })
            logging.info("Salmo %s: vídeo pronto em %s", number, result.video_path)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Falha ao processar Salmo %s", number)
            failures.append((number, str(exc)))

    if args.upload and to_upload:
        from .youtube_upload import upload_many

        logging.info("Enviando %d vídeo(s) ao YouTube...", len(to_upload))
        upload_results = upload_many(to_upload)
        for item, video_id, error in upload_results:
            if video_id:
                logging.info("Upload OK: %s -> https://youtu.be/%s", item["title"], video_id)
            else:
                logging.error("Upload falhou para %s: %s", item["title"], error)

    logging.info("Concluído: %d sucesso(s), %d falha(s).", len(successes), len(failures))
    for number, error in failures:
        logging.error("  Salmo %s: %s", number, error)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
