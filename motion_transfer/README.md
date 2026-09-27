# Motion Transfer — animar sua imagem gerada por IA com o movimento de um vídeo de referência

Pipeline open-source (ComfyUI + AnimateDiff + ControlNet + IPAdapter) que
pega:

1. uma **imagem** do seu personagem (que você mesmo gera por IA em outra
   ferramenta e entra aqui como referência), e
2. o **movimento** extraído de um vídeo de referência (pose de corpo inteiro),

e gera um vídeo do seu personagem executando aquele movimento — sem
reutilizar as imagens originais do vídeo de referência.

Ajustado para GPUs de **8GB de VRAM ou menos** (RTX 3050/3060 8GB, RTX 2070).

**Importante sobre fidelidade à imagem:** com esse conjunto de modelos
(SD1.5 + IPAdapter), o resultado fica *parecido* com sua imagem (rosto,
roupa, paleta, estilo), mas não é um clone pixel-perfeito em cada frame —
modelos de vídeo baseados em SD1.5 recriam a cena a cada frame guiados pela
sua imagem de referência, não "recortam e colam" ela. Existe uma classe de
modelos feita especificamente pra fidelidade maior a uma imagem única
(MimicMotion, MusePose) — ver seção **"Alternativa de maior fidelidade"**
no fim deste README — mas eles pedem tipicamente 16GB+ de VRAM, então
comece por aqui e migre só se precisar.

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
- `ComfyUI_IPAdapter_plus` (**necessário** — é o que faz o vídeo seguir a
  aparência da sua imagem, não só o texto do prompt)

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

1. **Load Video (Upload)** *(VideoHelperSuite)* → seu vídeo de referência
   (fonte do movimento).
2. **DWPose Estimator** *(comfyui_controlnet_aux)* → conecta na saída do passo 1.
   Isso gera o vídeo-esqueleto que guia o movimento.
3. **Load Image** → carregue aqui a **imagem do seu personagem** (a que você
   gerou por IA). Essa é a referência de identidade — o que faz o resultado
   parecer com o seu personagem.
4. **Load Checkpoint** → seu checkpoint SD1.5 (ex: DreamShaper 8).
5. **IPAdapter Unified Loader** + **Apply IPAdapter (Advanced)**
   *(ComfyUI_IPAdapter_plus)* → conecta a imagem do passo 3 e o model do
   checkpoint. Use `weight` entre **0.7 e 1.0** (quanto mais alto, mais fiel
   à sua imagem — mas alto demais engessa o movimento; ajuste testando).
6. **CLIP Text Encode (Prompt)** → aqui o texto vira só apoio de **cenário/
   iluminação**, não mais a descrição do personagem (ex: *"misty forest,
   cinematic lighting, high detail"*, já que o personagem já vem da imagem).
   Outro nó igual para o prompt negativo (ex: *"blurry, extra limbs,
   deformed, different person"*).
7. **AnimateDiff Loader** *(ComfyUI-AnimateDiff-Evolved)* → conecta no model
   (já com IPAdapter aplicado); carrega `mm_sd_v15_v2.ckpt`.
8. **Apply ControlNet (Advanced)** *(ComfyUI-Advanced-ControlNet)* → recebe
   o vídeo-esqueleto do passo 2 como imagem de controle, e o
   `control_v11p_sd15_openpose.pth` como modelo de controlnet.
9. **KSampler** → conecta model (IPAdapter + AnimateDiff aplicados),
   positive/negative conditioning (com ControlNet aplicado), latent vazio do
   tamanho da sua resolução escolhida.
10. **VAE Decode (Tiled)** → decodifica os frames gerados.
11. **Video Combine** *(VideoHelperSuite)* → junta os frames num `.mp4` final,
    no mesmo fps do vídeo de referência.

Clique **Queue Prompt** e valide o resultado. Se o personagem sair parecido
mas "genérico demais", suba o `weight` do IPAdapter; se sair travado/sem
seguir bem o movimento, desça um pouco.

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
`workflow_api.json`. Descubra os IDs dos nós de vídeo-de-pose, prompt,
imagem do personagem e saída (aparecem no JSON exportado) e ajuste
`jobs.example.json` com seus próprios vídeos de pose + prompts de cenário,
depois:

```bash
python batch_generate.py workflow_api.json jobs.example.json \
    --pose-node-id <ID_DO_LOAD_VIDEO> \
    --prompt-node-id <ID_DO_CLIP_TEXT_ENCODE> \
    --output-node-id <ID_DO_VIDEO_COMBINE> \
    --image-node-id <ID_DO_LOAD_IMAGE>   # só se for trocar o personagem entre jobs
```

Isso enfileira cada job no ComfyUI e espera a renderização terminar antes de
passar pro próximo — evita estourar a VRAM tentando rodar vários ao mesmo
tempo.

## Alternativa de maior fidelidade (MimicMotion / MusePose)

Se o resultado do IPAdapter não estiver parecido o suficiente com sua
imagem, existe uma categoria de modelos feita exatamente pra isso — recebem
**uma imagem de referência + uma sequência de pose** e geram vídeo mantendo
a identidade da imagem com muito mais fidelidade que IPAdapter (é o
propósito central do modelo, não um acessório).

- **MimicMotion** (Tencent) — https://github.com/Tencent/MimicMotion
- Wrapper para ComfyUI — https://github.com/kijai/ComfyUI-MimicMotionWrapper

⚠️ **Aviso de VRAM:** é baseado em Stable Video Diffusion, uma arquitetura
mais pesada que SD1.5. A documentação oficial recomenda ~16GB de VRAM na
configuração padrão. Em 8GB é bem provável esbarrar em `CUDA out of memory`
mesmo reduzindo resolução/frames — pode funcionar em resoluções bem baixas
(ex: 384×576) e poucos frames por lote, mas com bastante tentativa e erro.
Vale testar depois de validar o caminho principal (IPAdapter), não como
primeiro passo.

## Encaixe com o pipeline dos Salmos

Se a ideia é alimentar o canal do YouTube: o vídeo gerado aqui (corpo
inteiro, novo personagem, novo roteiro) pode substituir a imagem estática
usada em `salmos_video/` — dá pra adaptar `video_builder.py` pra aceitar um
vídeo de fundo em vez de uma imagem fixa, mantendo a narração e a thumbnail
como já estão. Posso montar essa integração quando esse pipeline estiver
validado na sua máquina.
