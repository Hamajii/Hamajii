"""Upload de vídeos para o YouTube via YouTube Data API v3.

Requer credenciais OAuth de um projeto no Google Cloud Console (gratuito):
veja instruções detalhadas no README.md, seção "Configurar upload pro YouTube".

Limite importante de cota: cada upload de vídeo custa 1600 unidades da cota
diária padrão de 10.000 unidades → por padrão só é possível enviar ~6 vídeos
por dia, salvo solicitação de aumento de cota ao Google.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import config


class YouTubeUploadError(RuntimeError):
    """Erro ao enviar vídeo para o YouTube."""


def _get_authenticated_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    if not config.YOUTUBE_CLIENT_SECRET_FILE.exists():
        raise YouTubeUploadError(
            "Arquivo client_secret.json não encontrado em "
            f"{config.YOUTUBE_CLIENT_SECRET_FILE}. Veja o README para criar as "
            "credenciais no Google Cloud Console (é gratuito)."
        )

    creds = None
    if config.YOUTUBE_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.YOUTUBE_TOKEN_FILE), config.YOUTUBE_UPLOAD_SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.YOUTUBE_CLIENT_SECRET_FILE), config.YOUTUBE_UPLOAD_SCOPES
            )
            creds = flow.run_local_server(port=0)
        config.YOUTUBE_TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    thumbnail_path: Path | None = None,
    tags: list[str] | None = None,
    privacy_status: str = config.YOUTUBE_DEFAULT_PRIVACY,
    category_id: str = config.YOUTUBE_DEFAULT_CATEGORY_ID,
) -> str:
    """Envia o vídeo (e opcionalmente a thumbnail). Retorna o videoId criado."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    service = _get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")

    try:
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
        video_id = response["id"]

        if thumbnail_path is not None and Path(thumbnail_path).exists():
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
            ).execute()

        return video_id
    except HttpError as exc:
        raise YouTubeUploadError(f"Falha no upload para o YouTube: {exc}") from exc


def upload_many(items: list[dict], delay_seconds: int = config.YOUTUBE_DELAY_BETWEEN_UPLOADS_SECONDS):
    """Envia vários vídeos em sequência, com pausa entre uploads.

    `items` é uma lista de dicts com as chaves aceitas por `upload_video`.
    Retorna lista de (item, video_id | None, erro | None).
    """
    results = []
    for i, item in enumerate(items):
        try:
            video_id = upload_video(**item)
            results.append((item, video_id, None))
        except Exception as exc:  # noqa: BLE001
            results.append((item, None, str(exc)))
        if i < len(items) - 1:
            time.sleep(delay_seconds)
    return results
