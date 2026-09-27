#!/usr/bin/env bash
# Instala o ComfyUI + os custom nodes necessários para o pipeline de
# transferência de movimento (pose de corpo inteiro) com AnimateDiff + ControlNet.
#
# Feito e testado para GPUs com ~8GB de VRAM (ex: RTX 3050/3060 8GB, RTX 2070).
# Requer: git, python3.10+, pip, e (fortemente recomendado) uma GPU NVIDIA
# com drivers CUDA instalados.
set -euo pipefail

INSTALL_DIR="${1:-$HOME/comfyui-motion-transfer}"
COMFY_DIR="$INSTALL_DIR/ComfyUI"

echo "==> Instalando em: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if [ -d "$COMFY_DIR" ]; then
  echo "==> ComfyUI já existe em $COMFY_DIR, atualizando..."
  git -C "$COMFY_DIR" pull
else
  echo "==> Clonando ComfyUI..."
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

cd "$COMFY_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo "==> Instalando PyTorch com suporte a CUDA..."
# Ajuste o índice de acordo com sua versão de CUDA se necessário:
# https://pytorch.org/get-started/locally/
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo "==> Instalando dependências do ComfyUI..."
pip install -r requirements.txt

CUSTOM_NODES="$COMFY_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES"

clone_node () {
  local repo_url="$1"
  local dir_name="$2"
  if [ -d "$CUSTOM_NODES/$dir_name" ]; then
    echo "==> $dir_name já existe, atualizando..."
    git -C "$CUSTOM_NODES/$dir_name" pull
  else
    echo "==> Clonando $dir_name..."
    git clone --depth 1 "$repo_url" "$CUSTOM_NODES/$dir_name"
  fi
  if [ -f "$CUSTOM_NODES/$dir_name/requirements.txt" ]; then
    pip install -r "$CUSTOM_NODES/$dir_name/requirements.txt"
  fi
}

# AnimateDiff (módulo de movimento) para SD1.5
clone_node "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git" "ComfyUI-AnimateDiff-Evolved"

# ControlNet avançado (necessário para condicionar pela pose extraída)
clone_node "https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git" "ComfyUI-Advanced-ControlNet"

# Nós de pré-processamento (extração de pose DWPose/OpenPose a partir do vídeo de referência)
clone_node "https://github.com/Fannovel16/comfyui_controlnet_aux.git" "comfyui_controlnet_aux"

# Carregar/combinar vídeo dentro do próprio ComfyUI (entrada e saída de vídeo)
clone_node "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "ComfyUI-VideoHelperSuite"

# IPAdapter (opcional, ajuda a manter a aparência do personagem consistente entre frames)
clone_node "https://github.com/cubiq/ComfyUI_IPAdapter_plus.git" "ComfyUI_IPAdapter_plus"

echo ""
echo "==> Estrutura de custom nodes instalada."
echo "==> Próximo passo: baixe os modelos listados em motion_transfer/models.md"
echo "    e coloque cada um na pasta indicada dentro de: $COMFY_DIR/models/"
echo ""
echo "==> Para iniciar o ComfyUI:"
echo "    cd $COMFY_DIR && source venv/bin/activate"
echo "    python main.py --lowvram --preview-method auto"
