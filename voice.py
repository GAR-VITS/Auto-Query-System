"""
Voice -> text transcription service.
"""
from __future__ import annotations

try:
    from config import get_settings
except ImportError:
    from app.core.config import get_settings

settings = get_settings()
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            import whisper
            _model = whisper.load_model(settings.whisper_model_size)
        except Exception as e:
            raise RuntimeError(f"Whisper speech recognition model could not be loaded: {e}")
    return _model


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribes an audio file to text."""
    if not settings.enable_voice_input:
        raise RuntimeError("Voice input is disabled in configuration.")
    model = _get_model()
    result = model.transcribe(audio_file_path)
    return result["text"].strip()
