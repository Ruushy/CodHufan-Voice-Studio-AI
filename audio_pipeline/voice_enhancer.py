import logging
import shutil
from pathlib import Path

logger = logging.getLogger('audio_pipeline')


def enhance_voice(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Enhancing voice quality: {input_path.name}")

    # Marka hore normalize si VoiceFixer uu si fiican u shaqeeyo
    normalized = input_path.parent / (input_path.stem + '_prenorm.wav')
    _pre_normalize(input_path, normalized)

    result = _enhance_with_voicefixer(normalized, output_path)
    if normalized.exists():
        normalized.unlink()
    if result['success']:
        return result

    logger.warning(f"VoiceFixer failed: {result.get('error')}. Trying EQ boost...")
    result = _enhance_with_eq(input_path, output_path)
    if result['success']:
        return result

    shutil.copy2(str(input_path), str(output_path))
    return {'success': True, 'output_path': str(output_path), 'method': 'passthrough'}


def _pre_normalize(input_path, output_path):
    """Codka -18 dBFS u normalize marka hore."""
    try:
        import soundfile as sf
        import numpy as np
        y, sr = sf.read(str(input_path))
        if y.ndim > 1:
            y = y.mean(axis=1)
        y = y.astype(np.float64)
        peak = np.max(np.abs(y))
        if peak > 0:
            target = 10 ** (-18.0 / 20.0)
            y = y * (target / peak)
        sf.write(str(output_path), y.astype(np.float32), sr, subtype='PCM_16')
        logger.info(f"Pre-normalized to -18 dBFS peak")
    except Exception as e:
        logger.warning(f"Pre-normalize failed: {e}, using original")
        shutil.copy2(str(input_path), str(output_path))


def _enhance_with_voicefixer(input_path, output_path):
    try:
        from voicefixer import VoiceFixer
    except ImportError:
        return {'success': False, 'error': 'VoiceFixer not installed'}

    try:
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Running VoiceFixer (mode 0) on {device}")

        vf = VoiceFixer()
        vf.restore(
            input=str(input_path),
            output=str(output_path),
            cuda=torch.cuda.is_available(),
            mode=0
        )

        if not output_path.exists():
            return {'success': False, 'error': 'VoiceFixer produced no output'}

        logger.info("VoiceFixer enhancement complete")
        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'voicefixer_mode0',
            'device': device
        }

    except Exception as e:
        logger.exception(f"VoiceFixer error: {e}")
        return {'success': False, 'error': str(e)}


def _enhance_with_eq(input_path, output_path):
    try:
        import numpy as np
        import soundfile as sf
        from scipy.signal import butter, sosfilt
    except ImportError:
        return {'success': False, 'error': 'scipy not installed'}

    try:
        logger.info("Applying parametric EQ enhancement")
        y, sr = sf.read(str(input_path))
        if y.ndim > 1:
            y = y.mean(axis=1)
        y = y.astype(np.float64)

        # High-pass 80Hz
        sos_hp = butter(2, 80 / (sr / 2), btype='high', output='sos')
        y = sosfilt(sos_hp, y)

        # Presence boost 2-5kHz
        sos_p = butter(2, [2000 / (sr / 2), 5000 / (sr / 2)], btype='band', output='sos')
        presence = sosfilt(sos_p, y)
        y = y + 0.5 * presence

        # Normalize
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y / peak * 0.85

        sf.write(str(output_path), y.astype(np.float32), sr, subtype='PCM_16')
        return {'success': True, 'output_path': str(output_path), 'method': 'parametric_eq'}

    except Exception as e:
        logger.exception(f"EQ error: {e}")
        return {'success': False, 'error': str(e)}
