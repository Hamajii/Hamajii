# Modelos necessários

Baixe cada arquivo abaixo e coloque na pasta indicada dentro de
`ComfyUI/models/` (caminho relativo à instalação criada pelo `setup.sh`).

Não consegui baixar esses arquivos por você nesta sessão — o ambiente de
desenvolvimento em nuvem onde eu rodo tem acesso de rede restrito e
`huggingface.co`/`civitai.com` estão bloqueados aqui. Baixe na sua máquina,
que tem acesso normal à internet.

## 1. Checkpoint base (SD1.5)

Qualquer checkpoint SD1.5 realista funciona. Sugestões:

- **Realistic Vision V6.0** — https://civitai.com/models/4201
- **DreamShaper 8** — https://huggingface.co/Lykon/dreamshaper-8

→ salvar em `models/checkpoints/`

## 2. Módulo de movimento AnimateDiff (SD1.5)

- **mm_sd_v15_v2.ckpt** — https://huggingface.co/guoyww/animatediff/blob/main/mm_sd_v15_v2.ckpt

→ salvar em `models/animatediff_models/`
(a pasta é criada automaticamente pelo custom node
ComfyUI-AnimateDiff-Evolved na primeira execução; se não existir, crie-a
manualmente)

## 3. ControlNet OpenPose (SD1.5)

- **control_v11p_sd15_openpose.pth** —
  https://huggingface.co/lllyasviel/ControlNet-v1-1/blob/main/control_v11p_sd15_openpose.pth

→ salvar em `models/controlnet/`

## 4. Modelos de detecção de pose (DWPose)

O nó `DWPose Estimator` (do `comfyui_controlnet_aux`) baixa automaticamente
os modelos `yolox_l.onnx` e `dw-ll_ucoco_384.onnx` na primeira vez que for
usado — só precisa de internet liberada na hora de rodar. Se preferir baixar
manualmente:

- https://huggingface.co/yzd-v/DWPose/tree/main

→ salvar em `custom_nodes/comfyui_controlnet_aux/ckpts/`

## 5. (Opcional) IPAdapter — consistência do personagem

Ajuda a manter a aparência do seu personagem igual em todos os frames,
usando uma imagem de referência dele.

- **ip-adapter_sd15.bin** —
  https://huggingface.co/h94/IP-Adapter/blob/main/models/ip-adapter_sd15.bin
  → `models/ipadapter/`
- **CLIP Vision (necessário para o IPAdapter)** —
  https://huggingface.co/h94/IP-Adapter/blob/main/models/image_encoder/model.safetensors
  → `models/clip_vision/` (renomeie para algo como `clip_vision_sd15.safetensors`)

## Tamanho total aproximado

~6-8 GB no total (checkpoint ~2GB, AnimateDiff ~1.7GB, ControlNet ~1.4GB,
DWPose ~400MB, IPAdapter opcional ~800MB). Garanta espaço em disco livre.
