# Motion Transfer — animar um personagem próprio com o movimento de um vídeo de referência

Pipeline open-source (ComfyUI + AnimateDiff + ControlNet) pra extrair a
**pose/movimento de corpo inteiro** de um vídeo de referência e aplicar esse
movimento num personagem/cena totalmente novos, gerados por IA — sem
reutilizar as imagens originais do vídeo de referência.

Ajustado para GPUs de **8GB de VRAM ou menos** (RTX 3050/3060 8GB, RTX 2070).

## Sobre o vídeo de referência (leia antes)

Este pipeline **não inclui nenhuma ferramenta de download** do Pinterest (ou
de qualquer outra plataforma) — isso foi uma decisão deliberada, não uma
lacuna a preencher depois. Você entra com um arquivo de vídeo local que já
tem em mãos. Extrair só o padrão de movimento (o "esqueleto" de pose) e gerar
um personagem/cena totalmente novos em cima disso é uma técnica normal em
animação (equivalente a usar um vídeo como referência de movimento/rotoscopia)
e bem mais defensável do que reusar o vídeo em si — mas isso não é um
parecer jurídico, é só o raciocínio por trás da escolha técnica. Se o vídeo
de referência tem uma coreografia/performance autoral muito específica e
reconhecível, considere isso antes de publicar o resultado.

## 1. Instalação

```bash
cd motion_transfer
./setup.sh ~/comfyui-motion-transfer
```

Isso clona o ComfyUI + instala os custom nodes:
- `ComfyUI-AnimateDiff-Evolved` (animação/motion module)
- `ComfyUI-Advanced-ControlNet` (condicionamento por pose)
- `comfyui_controlnet_aux` (extração de pose DWPose a partir do vídeo)
- `ComfyUI-VideoHelperSuite` (carregar vídeo de entrada / exportar vídeo de saída)
- `ComfyUI_IPAdapter_plus` (opcional — ajuda a manter o personagem consistente)

Depois baixe os modelos listados em **`models.md`** e coloque nas pastas indicadas.

## 2. Ajustes de VRAM para placas de 8GB

Ao iniciar o ComfyUI, use:

```bash
python main.py --lowvram --preview-method auto
```

E no workflow (passo 3), use estas configurações como ponto de partida:

| Parâmetro | Valor sugerido (8GB) |
|---|---|
| Resolução | 512×768 ou 512×512 |
| Duração por geração | 2-4 segundos (48-96 frames a 24fps) — vídeos mais longos, gere em blocos |
| Context length (AnimateDiff) | 16 frames, context overlap 4 |
| VAE | use "VAE Decode (Tiled)" em vez de "VAE Decode" comum |
| Sampler steps | 20-25 (mais que isso raramente compensa o tempo extra) |
| Attention | sdp (Scaled Dot Product) — já é o padrão em GPUs recentes |

Se ainda assim faltar memória (erro `CUDA out of memory`), reduza a
resolução para 448×640 ou o context length para 12.

## 3. Montar o workflow no ComfyUI (faça isso manualmente na primeira vez)

Não incluí um arquivo `.json` de workflow pronto porque não consigo validar
que ele carrega corretamente sem rodar o ComfyUI (o ambiente onde eu
desenvolvo isso não tem GPU nem acesso aos mesmos servidores). Montar na
interface uma vez é mais confiável — depois disso você **exporta** o grafo
validado e o reusa/automatiza.

Abra `http://127.0.0.1:8188` e monte os nós nesta ordem:

1. **Load Video (Upload)** *(VideoHelperSuite)* → seu vídeo de referência.
2. **DWPose Estimator** *(comfyui_controlnet_aux)* → conecta na saída do passo 1.
   Isso gera o vídeo-esqueleto que guia o movimento.
3. **Load Checkpoint** → seu checkpoint SD1.5 (ex: DreamShaper 8).
4. **CLIP Text Encode (Prompt)** → descreva o personagem/cena novos
   (ex: *"a knight in silver armor walking through a misty forest, cinematic
   lighting"*). Outro nó igual para o prompt negativo (ex: *"blurry, extra
   limbs, deformed"*).
5. **AnimateDiff Loader** *(ComfyUI-AnimateDiff-Evolved)* → conecta no model
   do checkpoint; carrega `mm_sd_v15_v2.ckpt`.
6. **Apply ControlNet (Advanced)** *(ComfyUI-Advanced-ControlNet)* → recebe
   o vídeo-esqueleto do passo 2 como imagem de controle, e o
   `control_v11p_sd15_openpose.pth` como modelo de controlnet.
7. **(Opcional) IPAdapter** → se quiser manter a aparência do personagem
   consistente, carregue uma imagem de referência dele aqui.
8. **KSampler** → conecta model (com AnimateDiff aplicado), positive/negative
   conditioning (com ControlNet aplicado), latent vazio do tamanho da sua
   resolução escolhida.
9. **VAE Decode (Tiled)** → decodifica os frames gerados.
10. **Video Combine** *(VideoHelperSuite)* → junta os frames num `.mp4` final,
    no mesmo fps do vídeo de referência.

Clique **Queue Prompt** e valide o resultado. Ajuste prompt/parâmetros até
ficar bom.

## 4. Preview rápido da extração de pose (opcional)

Antes de gastar tempo de geração, confira se a pose está sendo extraída de
forma limpa:

```bash
pip install -r requirements-extra.txt
python extract_pose.py referencia.mp4 pose_preview.mp4
```

Abra `pose_preview.mp4` — se o esqueleto estiver tremendo, cortando membros
ou perdendo o corpo em partes do vídeo, o resultado final também vai sair
ruim nesses trechos. Prefira vídeos de referência com boa iluminação, corpo
inteiro visível e sem cortes de câmera bruscos.

## 5. Automatizar em lote (depois de validar o workflow)

No ComfyUI, menu **Workflow → Export (API Format)** → salve como
`workflow_api.json`. Descubra os IDs dos nós de vídeo-de-pose, prompt e saída
(aparecem no JSON exportado) e ajuste `jobs.example.json` com seus próprios
vídeos de pose + prompts de personagem, depois:

```bash
python batch_generate.py workflow_api.json jobs.example.json \
    --pose-node-id <ID_DO_LOAD_VIDEO> \
    --prompt-node-id <ID_DO_CLIP_TEXT_ENCODE> \
    --output-node-id <ID_DO_VIDEO_COMBINE>
```

Isso enfileira cada job no ComfyUI e espera a renderização terminar antes de
passar pro próximo — evita estourar a VRAM tentando rodar vários ao mesmo
tempo.

## Encaixe com o pipeline dos Salmos

Se a ideia é alimentar o canal do YouTube: o vídeo gerado aqui (corpo
inteiro, novo personagem, novo roteiro) pode substituir a imagem estática
usada em `salmos_video/` — dá pra adaptar `video_builder.py` pra aceitar um
vídeo de fundo em vez de uma imagem fixa, mantendo a narração e a thumbnail
como já estão. Posso montar essa integração quando esse pipeline estiver
validado na sua máquina.
