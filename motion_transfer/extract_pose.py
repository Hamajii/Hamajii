"""Extrai o esqueleto de movimento (pose) de um vídeo de referência.

Gera um vídeo "stick figure" (esqueleto DWPose) frame a frame, que depois é
usado como entrada de ControlNet no workflow do ComfyUI. Útil para conferir
ANTES de rodar o pipeline completo se a extração de pose está limpa
(oclusões, câmera tremendo, etc. atrapalham o resultado final).

Este script é independente do ComfyUI (usa a biblioteca `controlnet_aux`
diretamente), então serve como preview rápido. O nó "DWPose Estimator" dentro
do ComfyUI faz a mesma coisa integrada ao workflow principal.

Uso:
    python extract_pose.py referencia.mp4 pose_saida.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm


def extract_pose_video(input_path: Path, output_path: Path, detect_hands: bool = True) -> None:
    from controlnet_aux import DWposeDetector

    print("Carregando modelo DWPose (baixa os pesos automaticamente na 1a vez)...")
    detector = DWposeDetector.from_pretrained("yzd-v/DWPose")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise SystemExit(f"Não foi possível abrir o vídeo: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    frame_iter = tqdm(range(total_frames), desc="Extraindo pose", unit="frame")
    for _ in frame_iter:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_frame = Image.fromarray(frame_rgb)

        pose_image = detector(pil_frame, include_hand=detect_hands, include_face=False)
        pose_rgb = np.array(pose_image.convert("RGB"))
        pose_bgr = cv2.cvtColor(pose_rgb, cv2.COLOR_RGB2BGR)
        if pose_bgr.shape[1::-1] != (width, height):
            pose_bgr = cv2.resize(pose_bgr, (width, height))
        writer.write(pose_bgr)

    cap.release()
    writer.release()
    print(f"Vídeo de pose salvo em: {output_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_video", type=Path, help="Vídeo de referência (movimento a copiar)")
    parser.add_argument("output_video", type=Path, help="Onde salvar o vídeo do esqueleto (mp4)")
    parser.add_argument("--no-hands", action="store_true", help="Desativa detecção de mãos")
    args = parser.parse_args(argv)

    if not args.input_video.exists():
        raise SystemExit(f"Arquivo não encontrado: {args.input_video}")

    extract_pose_video(args.input_video, args.output_video, detect_hands=not args.no_hands)
    return 0


if __name__ == "__main__":
    sys.exit(main())
