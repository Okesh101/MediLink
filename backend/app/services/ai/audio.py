# app/services/ai/audio.py

import os
from app.services.ai.client import client


def transcribe_voice_note(file_path: str) -> str:
    """
    Transcribes patient voice notes using Groq Whisper.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError("Audio file not found.")

    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="text"
        )
    return transcription
