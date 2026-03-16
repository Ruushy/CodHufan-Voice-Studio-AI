import logging
import shutil
from pathlib import Path

logger = logging.getLogger('audio_pipeline')


def master_audio(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Mastering audio: {input_path.name}")
    result = _master_full(input_path, output_path)
    if result['success']:
        return result
    shutil.copy2(str(input_path), str(output_path))
    return {'success': True, 'output_path': str(output_path), 'method': 'passthrough'}


def _master_full(input_path, output_path):
    try:
        import soundfile as sf
        import numpy as np
    except ImportError:
        return {'success': False, 'error': 'soundfile not installed'}

    try:
        data, rate = sf.read(str(input_path))
        if data.ndim > 1:
            data = data.mean(axis=1)
        data = data.astype(np.float64)

        if len(data) == 0 or np.max(np.abs(data)) == 0:
            return {'success': False, 'error': 'Audio is empty or silent'}

        # 1. High-pass filter
        try:
            from scipy.signal import butter, sosfilt
            sos_hp = butter(2, 80.0 / (rate / 2), btype='high', output='sos')
            data = sosfilt(sos_hp, data)
        except Exception:
            pass

        # 2. Gentle compression
        data = _compress(data, threshold_db=-20, ratio=2.5)

        # 3. Presence boost
        try:
            from scipy.signal import butter, sosfilt
            sos_p = butter(2, [2000.0 / (rate / 2), 5000.0 / (rate / 2)], btype='band', output='sos')
            presence = sosfilt(sos_p, data)
            data = data + 0.3 * presence
        except Exception:
            pass

        # 4. RMS normalize to -14 dBFS
        rms = np.sqrt(np.mean(data ** 2))
        if rms > 0:
            target_rms = 10 ** (-14.0 / 20.0)
            gain = min(target_rms / rms, 8.0)  # max +18 dB gain
            data = data * gain
            logger.info(f"Applied gain: {20*np.log10(gain):.1f} dB")

        # 5. Soft limiter
        limit = 0.891
        peak = np.max(np.abs(data))
        if peak > limit:
            # Soft clip badal hard clip
            data = np.tanh(data * (limit / peak)) * limit
            logger.info("Soft limiter applied")

        # 6. Log final
        final_rms = np.sqrt(np.mean(data ** 2))
        if final_rms > 0:
            logger.info(f"Output loudness: ~{20*np.log10(final_rms):.1f} dBFS RMS")

        sf.write(str(output_path), data.astype(np.float32), rate, subtype='PCM_16')
        logger.info("Mastering complete")

        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'ebu_r128_mastering',
        }

    except Exception as e:
        logger.exception(f"Mastering error: {e}")
        return {'success': False, 'error': str(e)}


def _compress(y, threshold_db=-20, ratio=2.5):
    import numpy as np
    threshold = 10 ** (threshold_db / 20.0)
    abs_y = np.abs(y)
    gain = np.ones_like(y)
    above = abs_y > threshold
    if np.any(above):
        gain[above] = (
            threshold + (abs_y[above] - threshold) / ratio
        ) / np.maximum(abs_y[above], 1e-10)
    return y * gain
