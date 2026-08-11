"""
Voice -> text step: "if Voice -> text, Whisper" in the diagram.

Uses openai-whisper locally (no API cost). Lazily loaded because the
model load is slow and most deployments will be text-only.
"""
from __future__ import annotations

from app.config import get_settings

settings = get_settings()

_model = None


def _get_model():
    global _model
    if _model is None:
        import whisper  # local import: heavy dependency, only needed for voice

        _model = whisper.load_model(settings.whisper_model_size)
    return _model


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribes an audio file (wav/mp3/m4a) to text."""
    if not settings.enable_voice_input:
        raise RuntimeError("Voice input is disabled. Set ENABLE_VOICE_INPUT=true in .env.")
    model = _get_model()
    result = model.transcribe(audio_file_path)
    return result["text"].strip()
