# Salmos Video — gerador em massa de vídeos devocionais

Pipeline 100% com ferramentas gratuitas que transforma um número de Salmo em
um vídeo pronto para o YouTube:

```
número do salmo
   -> texto em português (bible-api.com, gratuito)
   -> narração em áudio (edge-tts, gratuito)
   -> imagem de fundo gerada por IA (Pollinations.ai, gratuito, sem chave)
   -> thumbnail chamativa (Pillow)
   -> vídeo final com efeito Ken Burns (ffmpeg)
   -> [opcional] upload automático para o YouTube
```

## Instalação

```bash
pip install -r requirements.txt
```

Não é necessário instalar o `ffmpeg` no sistema: o pipeline usa o binário
estático baixado automaticamente pelo pacote `imageio-ffmpeg` (mas usa o
`ffmpeg` do sistema se ele já estiver no PATH).

## Uso básico

```bash
# Gera o vídeo do Salmo 23
python -m salmos_video.cli --psalms 23

# Gera vários de uma vez
python -m salmos_video.cli --psalms 1,23,91,150

# Gera uma faixa inteira (ótimo para produção em massa)
python -m salmos_video.cli --range 1-20 --output-dir output/lote1
```

Os arquivos gerados (`salmo_023.mp3`, `salmo_023_bg.jpg`, `salmo_023_thumb.jpg`,
`salmo_023.mp4`) vão para `output/`. Um `output/manifest.json` registra o que
já foi processado, então rodar o mesmo comando de novo **não regera** salmos
já feitos (use `--force` para regenerar).

## Configurar upload pro YouTube

O upload é opcional (`--upload`) e requer credenciais próprias do Google —
o Claude não pode criar isso por você, mas o processo é gratuito e leva
uns 10 minutos:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) e crie
   um projeto novo (ou use um existente).
2. Em **APIs e Serviços > Biblioteca**, ative a **YouTube Data API v3**.
3. Em **APIs e Serviços > Tela de consentimento OAuth**, configure como
   "Externo" e adicione seu e-mail como usuário de teste.
4. Em **APIs e Serviços > Credenciais**, crie uma credencial do tipo
   **ID do cliente OAuth**, tipo de app **Aplicativo para computador**.
5. Baixe o JSON gerado e salve como `credentials/client_secret.json`
   (esse caminho já está no `.gitignore` — nunca vai pro Git).
6. Na primeira execução com `--upload`, uma janela do navegador vai abrir
   pedindo login/autorização; depois disso um `credentials/token.json` é
   salvo e os próximos uploads não pedem login de novo.

```bash
python -m salmos_video.cli --psalms 23 --upload --privacy unlisted
```

### ⚠️ Cota da API e política de conteúdo — leia antes de "subir em massa"

- **Cota diária:** cada upload de vídeo consome 1600 das 10.000 unidades
  gratuitas por dia → **~6 vídeos/dia** por padrão. Para mais, é preciso
  solicitar aumento de cota ao Google (formulário gratuito, mas com análise).
- **Política do YouTube sobre conteúdo em massa/repetitivo:** desde 2024 o
  YouTube reforçou regras contra conteúdo "reaproveitado" ou produzido em
  massa de forma pouco diferenciada (isso pode afetar monetização e, em
  casos extremos, o canal). Recomendado:
  - Variar imagens/temas visuais (o pipeline já roda uma rotação de cenários
    diferentes por salmo, ver `VISUAL_THEMES` em `pipeline.py`).
  - Espaçar os envios (não sobe tudo de uma vez; use o parâmetro
    `--privacy unlisted` para revisar antes de tornar público).
  - Considerar adicionar valor extra (legendas, introdução falada,
    descrição bem escrita) em vez de só narração + imagem estática.

## Personalização

Praticamente todo o comportamento fica em `salmos_video/config.py`:
tradução da Bíblia, voz do TTS, estilo/prompt da imagem gerada, resolução,
velocidade do efeito Ken Burns, categoria/privacidade padrão no YouTube, etc.

## Observação sobre este ambiente de desenvolvimento

Este container de execução tem uma política de rede restrita (allowlist) que
bloqueia chamadas diretas a `bible-api.com`, `image.pollinations.ai` e
serviços de TTS — por isso essas integrações **não puderam ser testadas
"ao vivo" aqui**. O código segue os formatos documentados dessas APIs
públicas e tem fallbacks (ex.: gera um gradiente local se a imagem por IA
falhar), mas rode e valide localmente com:

```bash
python -m salmos_video.cli --psalms 23 -v
```

para confirmar que tudo funciona na sua máquina com acesso normal à internet.
