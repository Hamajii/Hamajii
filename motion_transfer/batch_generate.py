"""Automatiza a geração em lote via API HTTP do ComfyUI.

IMPORTANTE: só use isso depois de validar manualmente o workflow na
interface do ComfyUI (veja README.md). Este script assume que você já tem
um workflow funcionando, exportado em formato "API" (Save (API Format) no
menu do ComfyUI), com os IDs de nó indicados em `--pose-node-id` e
`--prompt-node-id` apontando para os nós certos no seu grafo.

Uso:
    python batch_generate.py workflow_api.json jobs.json --comfyui-url http://127.0.0.1:8188
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
import urllib.request
from pathlib import Path


class ComfyUIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def queue_prompt(self, workflow: dict) -> str:
        data = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/prompt", data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        return result["prompt_id"]

    def wait_for_completion(self, prompt_id: str, poll_seconds: float = 3.0, timeout: float = 1800.0) -> dict:
        start = time.time()
        while time.time() - start < timeout:
            with urllib.request.urlopen(f"{self.base_url}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(poll_seconds)
        raise TimeoutError(f"Geração {prompt_id} não terminou em {timeout}s")


def load_jobs(jobs_path: Path) -> list[dict]:
    """Cada job no JSON deve ter:
    {"pose_video": "...", "character_image": "...", "prompt": "...", "output_prefix": "..."}.

    `character_image` é opcional por job: se omitido, mantém a imagem já
    carregada no nó "Load Image" do workflow base.
    """
    return json.loads(jobs_path.read_text())


def apply_job_to_workflow(
    base_workflow: dict,
    job: dict,
    pose_node_id: str,
    prompt_node_id: str,
    output_node_id: str,
    image_node_id: str | None = None,
) -> dict:
    workflow = copy.deepcopy(base_workflow)

    if pose_node_id in workflow:
        workflow[pose_node_id]["inputs"]["video"] = job["pose_video"]
    if prompt_node_id in workflow:
        workflow[prompt_node_id]["inputs"]["text"] = job["prompt"]
    if output_node_id in workflow and "output_prefix" in job:
        workflow[output_node_id]["inputs"]["filename_prefix"] = job["output_prefix"]
    if image_node_id and image_node_id in workflow and "character_image" in job:
        workflow[image_node_id]["inputs"]["image"] = job["character_image"]

    return workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_api_json", type=Path, help="Workflow exportado em 'API Format'")
    parser.add_argument("jobs_json", type=Path, help="Lista de jobs (vídeo de pose + prompt do personagem)")
    parser.add_argument("--comfyui-url", default="http://127.0.0.1:8188")
    parser.add_argument("--pose-node-id", default="10", help="ID do nó 'Load Video' da pose no grafo")
    parser.add_argument("--prompt-node-id", default="6", help="ID do nó CLIPTextEncode (cenário/iluminação)")
    parser.add_argument("--output-node-id", default="20", help="ID do nó de saída de vídeo (VHS_VideoCombine)")
    parser.add_argument("--image-node-id", default=None, help="ID do nó 'Load Image' do personagem (opcional, só se variar por job)")
    args = parser.parse_args(argv)

    base_workflow = json.loads(args.workflow_api_json.read_text())
    jobs = load_jobs(args.jobs_json)
    client = ComfyUIClient(args.comfyui_url)

    print(f"Enfileirando {len(jobs)} job(s)...")
    for i, job in enumerate(jobs, start=1):
        workflow = apply_job_to_workflow(
            base_workflow, job, args.pose_node_id, args.prompt_node_id, args.output_node_id, args.image_node_id
        )
        prompt_id = client.queue_prompt(workflow)
        print(f"[{i}/{len(jobs)}] enfileirado (prompt_id={prompt_id}), aguardando renderização...")
        client.wait_for_completion(prompt_id)
        print(f"[{i}/{len(jobs)}] concluído.")

    print("Lote concluído.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
