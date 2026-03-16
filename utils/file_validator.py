"""
File validation utilities for uploaded audio/video files.
"""
from pathlib import Path

MAX_FILE_SIZE_MB = 500
ALLOWED_EXTENSIONS = {
    '.mp4', '.mov', '.mkv', '.avi', '.webm',  # video
    '.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a',  # audio
}
ALLOWED_MIME_TYPES = {
    'video/mp4', 'video/quicktime', 'video/x-matroska',
    'video/x-msvideo', 'video/webm',
    'audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3',
    'audio/flac', 'audio/aac', 'audio/ogg', 'audio/mp4',
    'audio/x-m4a', 'application/octet-stream',
}


def validate_upload(file_obj) -> dict:
    """
    Validate an uploaded file for type, size, and basic sanity.
    Returns {'valid': bool, 'error': str | None}
    """
    filename = file_obj.name or ''
    ext = Path(filename).suffix.lower()

    if not ext:
        return {'valid': False, 'error': 'File has no extension'}

    if ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        return {
            'valid': False,
            'error': f'File type "{ext}" is not supported. Allowed: {allowed}'
        }

    size_mb = file_obj.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            'valid': False,
            'error': f'File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit'
        }

    if file_obj.size < 1024:
        return {'valid': False, 'error': 'File appears to be empty or too small'}

    return {'valid': True, 'error': None}
