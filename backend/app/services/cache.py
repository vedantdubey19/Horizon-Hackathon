import hashlib
from typing import Dict, List, Optional
from app.schemas import TranscribedStep

# In-memory transcription cache keyed by SHA-256 hash of image bytes
_TRANSCRIPTION_CACHE: Dict[str, List[TranscribedStep]] = {}


def compute_image_hash(image_bytes: bytes) -> str:
    """Compute SHA-256 hash of image content."""
    return hashlib.sha256(image_bytes).hexdigest()


def get_cached_transcription(image_hash: str) -> Optional[List[TranscribedStep]]:
    """Retrieve cached transcription if present."""
    return _TRANSCRIPTION_CACHE.get(image_hash)


def cache_transcription(image_hash: str, steps: List[TranscribedStep]) -> None:
    """Store transcription steps in cache."""
    _TRANSCRIPTION_CACHE[image_hash] = steps


def clear_cache() -> None:
    """Clear in-memory cache (primarily for test teardown)."""
    _TRANSCRIPTION_CACHE.clear()
