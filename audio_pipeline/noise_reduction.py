"""
Stage 3: Noise Reduction
Removes microphone hiss, electrical hum, room noise, and environmental artifacts.
Primary: DeepFilterNet | Fallback: noisereduce (spectral subtraction)
"""
import logging
import shutil
from pathlib import Path

logger = logging.getLogger('audio_pipeline')


def reduce_noise(input_path: str, output_path: str) -> dict:
    """
    Apply noise reduction to isolated voice audio.
    
    Args:
        input_path: Path to voice-isolated WAV
        output_path: Path to save noise-reduced WAV
        
    Returns:
        dict with success status and metadata
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Applying noise reduction to: {input_path.name}")

    # Try DeepFilterNet (neural network, best quality)
    result = _reduce_with_deepfilter(input_path, output_path)
    if result['success']:
        return result

    logger.warning(f"DeepFilterNet failed: {result.get('error')}. Trying noisereduce...")

    # Fallback: spectral noise gating via noisereduce
    result = _reduce_with_noisereduce(input_path, output_path)
    if result['success']:
        return result

    logger.warning("Noise reduction libraries unavailable. Using scipy-based filtering...")

    # Last resort: basic high-pass filter to remove hum
    result = _reduce_with_scipy(input_path, output_path)
    if result['success']:
        return result

    logger.warning("All noise reduction methods failed. Passing through unchanged.")
    shutil.copy2(str(input_path), str(output_path))
    return {
        'success': True,
        'output_path': str(output_path),
        'method': 'passthrough',
        'note': 'Noise reduction skipped — libraries unavailable'
    }


def _reduce_with_deepfilter(input_path: Path, output_path: Path) -> dict:
    """Use DeepFilterNet2 for neural noise suppression."""
    try:
        from df.enhance import enhance, init_df, load_audio, save_audio
    except ImportError:
        return {'success': False, 'error': 'DeepFilterNet (df) not installed'}

    try:
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Running DeepFilterNet on {device}")

        model, df_state, _ = init_df()
        audio, _ = load_audio(str(input_path), sr=df_state.sr())
        enhanced = enhance(model, df_state, audio)
        save_audio(str(output_path), enhanced, df_state.sr())

        logger.info("DeepFilterNet noise reduction complete")
        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'deepfilternet2',
            'device': device
        }

    except Exception as e:
        logger.exception(f"DeepFilterNet error: {e}")
        return {'success': False, 'error': str(e)}


def _reduce_with_noisereduce(input_path: Path, output_path: Path) -> dict:
    """Spectral noise reduction using the noisereduce library."""
    try:
        import noisereduce as nr
        import librosa
        import soundfile as sf
        import numpy as np
    except ImportError:
        return {'success': False, 'error': 'noisereduce or librosa not installed'}

    try:
        logger.info("Running noisereduce spectral subtraction")
        y, sr = librosa.load(str(input_path), sr=None, mono=True)

        # Use first 0.5 seconds as noise profile (if available)
        noise_sample_duration = min(int(sr * 0.5), len(y) // 10)
        noise_clip = y[:noise_sample_duration] if noise_sample_duration > 0 else None

        if noise_clip is not None and len(noise_clip) > 100:
            reduced = nr.reduce_noise(
                y=y, sr=sr,
                y_noise=noise_clip,
                prop_decrease=0.75,  # aggressive but not destructive
                stationary=False
            )
        else:
            reduced = nr.reduce_noise(y=y, sr=sr, stationary=True, prop_decrease=0.6)

        # Normalize
        max_val = np.max(np.abs(reduced))
        if max_val > 0:
            reduced = reduced / max_val * 0.9

        sf.write(str(output_path), reduced, sr, subtype='PCM_16')

        logger.info("noisereduce spectral subtraction complete")
        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'noisereduce_spectral'
        }

    except Exception as e:
        logger.exception(f"noisereduce error: {e}")
        return {'success': False, 'error': str(e)}


def _reduce_with_scipy(input_path: Path, output_path: Path) -> dict:
    """Basic noise reduction using scipy filters (last resort)."""
    try:
        import numpy as np
        import soundfile as sf
        from scipy.signal import butter, sosfilt
    except ImportError:
        return {'success': False, 'error': 'scipy/soundfile not installed'}

    try:
        logger.info("Running scipy basic filtering")
        y, sr = sf.read(str(input_path))
        if y.ndim > 1:
            y = y.mean(axis=1)

        # High-pass at 80Hz to remove hum/rumble
        sos_hp = butter(4, 80 / (sr / 2), btype='high', output='sos')
        y = sosfilt(sos_hp, y)

        # Low-pass at 8000Hz to reduce hiss (voice is 80–8000 Hz)
        sos_lp = butter(4, 8000 / (sr / 2), btype='low', output='sos')
        y = sosfilt(sos_lp, y)

        # Normalize
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val * 0.9

        sf.write(str(output_path), y.astype(np.float32), sr, subtype='PCM_16')

        logger.info("scipy basic filtering complete")
        return {
            'success': True,
            'output_path': str(output_path),
            'method': 'scipy_basic_filter'
        }

    except Exception as e:
        logger.exception(f"scipy error: {e}")
        return {'success': False, 'error': str(e)}
