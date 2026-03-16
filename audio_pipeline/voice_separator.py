import logging
import shutil
from pathlib import Path

logger = logging.getLogger('audio_pipeline')


def isolate_voice(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Isolating voice from: {input_path.name}")

    # Skip Demucs entirely - too slow on CPU
    # Go straight to fast librosa method
    result = _isolate_with_librosa(input_path, output_path)
    if result['success']:
        return result

    # If librosa fails just copy the file
    logger.warning("Librosa failed. Passing through.")
    shutil.copy2(str(input_path), str(output_path))
    return {
        'success': True,
        'output_path': str(output_path),
        'method': 'passthrough'
    }


def _isolate_with_librosa(input_path, output_path):
    try:
        import librosa
        import soundfile as sf
        import numpy as np
    except ImportError:
        return {'success': False, 'error': 'librosa not installed'}

    try:
        logger.info("Running fast librosa HPSS")
        y, sr = librosa.load(str(input_path), sr=None, mono=True)
        D = librosa.stft(y)
        D_harmonic, _ = librosa.decompose.hpss(D, margin=3.0)
        y_harmonic = librosa.istft(D_harmonic, length=len(y))

        max_val = np.max(np.abs(y_harmonic))
        if max_val > 0:
            y_harmonic = y_harmonic / max_val * 0.9

        sf.write(str(output_path), y_harmonic, sr, subtype='PCM_16')

        logger.info("Librosa HPSS done")
        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'librosa_hpss'
        }

    except Exception as e:
        logger.exception(f"Librosa error: {e}")
        return {'success': False, 'error': str(e)}
