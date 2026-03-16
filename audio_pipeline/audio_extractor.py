import os
import shutil
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger('audio_pipeline')


def _find_ffmpeg():
    found = shutil.which('ffmpeg')
    if found:
        return found
    candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _find_ffprobe():
    found = shutil.which('ffprobe')
    if found:
        return found
    candidates = [
        r'C:\ffmpeg\bin\ffprobe.exe',
        r'C:\Program Files\ffmpeg\bin\ffprobe.exe',
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def extract_audio(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = input_path.suffix.lower()
    video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.webm'}
    audio_extensions = {'.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a'}

    if ext not in video_extensions and ext not in audio_extensions:
        return {'success': False, 'error': f'Unsupported file type: {ext}'}

    ffmpeg_exe = _find_ffmpeg()
    if not ffmpeg_exe:
        return {
            'success': False,
            'error': 'FFmpeg not found. Make sure C:\\ffmpeg\\bin\\ffmpeg.exe exists.'
        }

    logger.info(f"Using FFmpeg at: {ffmpeg_exe}")
    logger.info(f"Extracting audio from: {input_path.name}")

    cmd = [
        ffmpeg_exe,
        '-i', str(input_path),
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '1',
        '-y',
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return {
                'success': False,
                'error': f'FFmpeg failed: {result.stderr[-300:]}'
            }

        if not output_path.exists() or output_path.stat().st_size == 0:
            return {'success': False, 'error': 'Output file is empty or missing'}

        duration = _get_audio_duration(str(output_path))
        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        logger.info(f"Audio extracted. Duration: {duration:.1f}s")
        return {
            'success': True,
            'output_path': str(output_path),
            'duration_seconds': duration,
            'file_size_mb': round(file_size_mb, 2),
            'sample_rate': 44100,
            'channels': 1,
        }

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Audio extraction timed out'}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {'success': False, 'error': str(e)}


def _get_audio_duration(wav_path):
    try:
        ffprobe_exe = _find_ffprobe()
        if not ffprobe_exe:
            return 0.0
        cmd = [
            ffprobe_exe,
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            wav_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0
