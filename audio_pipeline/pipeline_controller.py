"""
Pipeline Controller
Orchestrates the full audio processing pipeline:
Stage 1 → Extract → Stage 2 → Isolate → Stage 3 → Denoise → Stage 4 → Enhance → Stage 5 → Master
"""
import os
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger('audio_pipeline')


class VoiceProcessingPipeline:
    """
    Orchestrates the complete voice enhancement pipeline.
    Handles stage management, progress callbacks, and error recovery.
    """

    STAGES = [
        (1, 'Extracting audio', 0),
        (2, 'Isolating voice', 20),
        (3, 'Removing noise', 40),
        (4, 'Enhancing voice', 60),
        (5, 'Mastering audio', 80),
        (6, 'Finalizing', 95),
    ]

    def __init__(self, job_id: str, upload_path: str, output_dir: str,
                 progress_callback=None):
        """
        Args:
            job_id: Unique identifier for this processing job
            upload_path: Path to uploaded file
            output_dir: Directory to store intermediate and final files
            progress_callback: Optional callable(stage_num, stage_name, percent, detail)
        """
        self.job_id = job_id
        self.upload_path = Path(upload_path)
        self.output_dir = Path(output_dir)
        self.progress_callback = progress_callback
        self.results = {}
        self.start_time = None

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _stage_path(self, name: str) -> Path:
        return self.output_dir / f"{self.job_id}_{name}.wav"

    def _report(self, stage: int, name: str, percent: int, detail: str = ''):
        logger.info(f"[{self.job_id}] Stage {stage}: {name} ({percent}%) {detail}")
        if self.progress_callback:
            try:
                self.progress_callback(stage, name, percent, detail)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def run(self) -> dict:
        """Execute the full pipeline. Returns comprehensive result dict."""
        self.start_time = time.time()
        logger.info(f"=== Starting pipeline for job {self.job_id} ===")
        logger.info(f"Input: {self.upload_path}")

        try:
            result = self._run_pipeline()
        except Exception as e:
            logger.exception(f"Fatal pipeline error: {e}")
            result = {
                'success': False,
                'error': f'Pipeline failed unexpectedly: {str(e)}',
                'stage_failed': 'unknown',
            }

        result['job_id'] = self.job_id
        result['elapsed_seconds'] = round(time.time() - self.start_time, 1)
        result['stage_results'] = self.results
        result['timestamp'] = datetime.utcnow().isoformat()

        if result['success']:
            logger.info(f"=== Pipeline complete in {result['elapsed_seconds']}s ===")
        else:
            logger.error(f"=== Pipeline FAILED: {result.get('error')} ===")

        return result

    def _run_pipeline(self) -> dict:
        from audio_pipeline.audio_extractor import extract_audio
        from audio_pipeline.voice_separator import isolate_voice
        from audio_pipeline.noise_reduction import reduce_noise
        from audio_pipeline.voice_enhancer import enhance_voice
        from audio_pipeline.audio_mastering import master_audio

        # ── Stage 1: Audio Extraction ──────────────────────────────────────
        self._report(1, 'Extracting audio', 5)
        raw_wav = self._stage_path('s1_raw')
        r = extract_audio(str(self.upload_path), str(raw_wav))
        self.results['extraction'] = r
        if not r['success']:
            return {'success': False, 'error': r['error'], 'stage_failed': 'extraction'}
        self._report(1, 'Extracting audio', 18, f"Duration: {r.get('duration_seconds', 0):.1f}s")

        # ── Stage 2: Voice Isolation ───────────────────────────────────────
        self._report(2, 'Isolating voice', 20)
        isolated_wav = self._stage_path('s2_isolated')
        r = isolate_voice(str(raw_wav), str(isolated_wav))
        self.results['isolation'] = r
        if not r['success']:
            return {'success': False, 'error': r['error'], 'stage_failed': 'isolation'}
        self._report(2, 'Isolating voice', 38, f"Method: {r.get('method', 'n/a')}")

        # ── Stage 3: Noise Reduction ───────────────────────────────────────
        self._report(3, 'Removing noise', 40)
        denoised_wav = self._stage_path('s3_denoised')
        r = reduce_noise(str(isolated_wav), str(denoised_wav))
        self.results['noise_reduction'] = r
        if not r['success']:
            return {'success': False, 'error': r['error'], 'stage_failed': 'noise_reduction'}
        self._report(3, 'Removing noise', 58, f"Method: {r.get('method', 'n/a')}")

        # ── Stage 4: Voice Enhancement ─────────────────────────────────────
        self._report(4, 'Enhancing voice', 60)
        enhanced_wav = self._stage_path('s4_enhanced')
        r = enhance_voice(str(denoised_wav), str(enhanced_wav))
        self.results['enhancement'] = r
        if not r['success']:
            return {'success': False, 'error': r['error'], 'stage_failed': 'enhancement'}
        self._report(4, 'Enhancing voice', 78, f"Method: {r.get('method', 'n/a')}")

        # ── Stage 5: Audio Mastering ───────────────────────────────────────
        self._report(5, 'Mastering audio', 80)
        final_wav = self._stage_path('final_studio')
        r = master_audio(str(enhanced_wav), str(final_wav))
        self.results['mastering'] = r
        if not r['success']:
            return {'success': False, 'error': r['error'], 'stage_failed': 'mastering'}
        self._report(5, 'Mastering audio', 93, f"Method: {r.get('method', 'n/a')}")

        # ── Finalize ───────────────────────────────────────────────────────
        self._report(6, 'Finalizing', 97)
        self._cleanup_intermediates([raw_wav, isolated_wav, denoised_wav, enhanced_wav])

        final_size_mb = round(final_wav.stat().st_size / (1024 * 1024), 2) if final_wav.exists() else 0

        return {
            'success': True,
            'output_path': str(final_wav),
            'output_filename': final_wav.name,
            'file_size_mb': final_size_mb,
            'duration_seconds': self.results['extraction'].get('duration_seconds', 0),
            'methods_used': {
                'extraction': self.results.get('extraction', {}).get('method', 'ffmpeg'),
                'isolation': self.results.get('isolation', {}).get('method', 'n/a'),
                'noise_reduction': self.results.get('noise_reduction', {}).get('method', 'n/a'),
                'enhancement': self.results.get('enhancement', {}).get('method', 'n/a'),
                'mastering': self.results.get('mastering', {}).get('method', 'n/a'),
            }
        }

    def _cleanup_intermediates(self, paths: list):
        """Remove intermediate files to save disk space."""
        for p in paths:
            try:
                if Path(p).exists():
                    Path(p).unlink()
                    logger.debug(f"Cleaned up intermediate: {p}")
            except Exception as e:
                logger.warning(f"Could not delete intermediate {p}: {e}")


def run_pipeline(job_id: str, upload_path: str, output_dir: str,
                 progress_callback=None) -> dict:
    """Convenience function to run the full pipeline."""
    pipeline = VoiceProcessingPipeline(
        job_id=job_id,
        upload_path=upload_path,
        output_dir=output_dir,
        progress_callback=progress_callback
    )
    return pipeline.run()
