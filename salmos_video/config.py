"""Configuração central do pipeline de vídeos de Salmos."""
from pathlib import Path

# --- Diretórios ---
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CREDENTIALS_DIR = BASE_DIR / "credentials"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

# --- Texto bíblico ---
# bible-api.com é gratuita e não exige chave de API.
# Referência em inglês ("Psalms") + translation=almeida devolve o texto
# em português (tradução João Ferreira de Almeida).
BIBLE_API_BASE = "https://bible-api.com"
DEFAULT_TRANSLATION = "almeida"
# Formatos de referência tentados em ordem até um funcionar.
BIBLE_REFERENCE_TEMPLATES = ["Psalms {n}", "Salmos {n}", "Psalms+{n}"]

# --- Narração (TTS) ---
# edge-tts é gratuito (usa as vozes neurais do Microsoft Edge "Ler em voz alta").
TTS_ENGINE = "edge-tts"  # "edge-tts" ou "gtts"
TTS_VOICE = "pt-BR-AntonioNeural"  # alternativa feminina: pt-BR-FranciscaNeural
TTS_RATE = "-5%"  # levemente mais lento, tom mais contemplativo
TTS_PITCH = "-2Hz"

# --- Imagem de fundo (geração de imagem gratuita, sem chave) ---
IMAGE_API_BASE = "https://image.pollinations.ai/prompt"
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
IMAGE_MODEL = "flux"  # modelo padrão do Pollinations
IMAGE_STYLE_SUFFIX = (
    "biblical epic landscape, golden hour light, cinematic, painterly, "
    "serene and majestic, no text, no watermark, no people close-up faces"
)

# --- Thumbnail ---
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720
# Fontes candidatas em ordem de preferência (a primeira que existir é usada).
FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

# --- Vídeo ---
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
KEN_BURNS_MAX_ZOOM = 1.15
KEN_BURNS_SPEED = 0.0006  # incremento de zoom por frame
VIDEO_BITRATE_AUDIO = "192k"

# --- YouTube upload ---
YOUTUBE_CLIENT_SECRET_FILE = CREDENTIALS_DIR / "client_secret.json"
YOUTUBE_TOKEN_FILE = CREDENTIALS_DIR / "token.json"
YOUTUBE_UPLOAD_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_DEFAULT_PRIVACY = "private"  # "private" | "unlisted" | "public"
YOUTUBE_DEFAULT_CATEGORY_ID = "22"  # People & Blogs
# Custo de cada upload é 1600 unidades; cota padrão diária é 10000 unidades
# (~6 uploads/dia) até que se solicite aumento de cota no Google Cloud Console.
YOUTUBE_DELAY_BETWEEN_UPLOADS_SECONDS = 30
