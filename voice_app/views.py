import os
import uuid
import logging
import threading
from pathlib import Path

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import ProcessingJob
from utils.file_validator import validate_upload

logger = logging.getLogger('audio_pipeline')


def index(request):
    """Upload page — home."""
    recent_jobs = ProcessingJob.objects.filter(
        status=ProcessingJob.Status.COMPLETE
    )[:5]
    return render(request, 'voice_app/index.html', {'recent_jobs': recent_jobs})


@require_POST
def upload_file(request):
    """Handle file upload, create job, start async processing."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    uploaded_file = request.FILES['file']

    # Validate
    validation = validate_upload(uploaded_file)
    if not validation['valid']:
        return JsonResponse({'error': validation['error']}, status=400)

    # Save upload
    job_id = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(uploaded_file.name).suffix.lower()
    safe_filename = f"{job_id}{ext}"
    upload_path = upload_dir / safe_filename

    with open(upload_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    # Create job record
    job = ProcessingJob.objects.create(
        id=job_id,
        original_filename=uploaded_file.name,
        upload_path=str(upload_path),
        status=ProcessingJob.Status.PENDING,
        file_size_mb=round(uploaded_file.size / (1024 * 1024), 2),
    )

    # Start processing in background thread
    thread = threading.Thread(
        target=_process_job,
        args=(job_id, str(upload_path)),
        daemon=True
    )
    thread.start()

    return JsonResponse({
        'job_id': job_id,
        'redirect_url': f'/job/{job_id}/',
    })


def job_status(request, job_id):
    """Processing status page."""
    job = get_object_or_404(ProcessingJob, id=job_id)
    return render(request, 'voice_app/processing.html', {'job': job})


def job_result(request, job_id):
    """Result page with audio players and download."""
    job = get_object_or_404(ProcessingJob, id=job_id)
    if job.status != ProcessingJob.Status.COMPLETE:
        return redirect('job_status', job_id=job_id)
    return render(request, 'voice_app/result.html', {'job': job})


@require_GET
def api_job_status(request, job_id):
    """JSON API for polling job status."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
    except ProcessingJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    data = {
        'job_id': str(job.id),
        'status': job.status,
        'progress_percent': job.progress_percent,
        'current_stage': job.current_stage,
        'error_message': job.error_message,
        'output_url': job.output_url,
        'upload_url': job.upload_url,
        'duration_formatted': job.duration_formatted,
        'elapsed_seconds': job.elapsed_seconds,
        'methods_used': job.methods_used,
        'result_url': f'/job/{job.id}/result/' if job.status == 'complete' else None,
    }
    return JsonResponse(data)


def download_file(request, job_id):
    """Serve the processed file as a download."""
    job = get_object_or_404(ProcessingJob, id=job_id, status=ProcessingJob.Status.COMPLETE)

    if not job.output_path or not Path(job.output_path).exists():
        raise Http404("Processed file not found")

    response = FileResponse(
        open(job.output_path, 'rb'),
        content_type='audio/wav',
        as_attachment=True,
        filename=f"codHufan_{job.original_filename.rsplit('.', 1)[0]}.wav"
    )
    return response


def jobs_list(request):
    """List all jobs."""
    jobs = ProcessingJob.objects.all()[:50]
    return render(request, 'voice_app/jobs.html', {'jobs': jobs})


# ── Background Processing ─────────────────────────────────────────────────────

def _process_job(job_id: str, upload_path: str):
    """Run the pipeline in a background thread."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        job.status = ProcessingJob.Status.PROCESSING
        job.save()

        output_dir = settings.PROCESSED_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        def progress_callback(stage, stage_name, percent, detail=''):
            try:
                ProcessingJob.objects.filter(id=job_id).update(
                    progress_percent=percent,
                    current_stage=stage_name,
                )
            except Exception as e:
                logger.warning(f"Progress update failed: {e}")

        from audio_pipeline.pipeline_controller import run_pipeline
        result = run_pipeline(
            job_id=job_id,
            upload_path=upload_path,
            output_dir=str(output_dir),
            progress_callback=progress_callback
        )

        job = ProcessingJob.objects.get(id=job_id)
        if result['success']:
            job.status = ProcessingJob.Status.COMPLETE
            job.output_path = result['output_path']
            job.progress_percent = 100
            job.current_stage = 'Complete'
            job.duration_seconds = result.get('duration_seconds')
            job.elapsed_seconds = result.get('elapsed_seconds')
            job.methods_used = result.get('methods_used', {})
            job.processing_log = result.get('stage_results', {})
            job.completed_at = timezone.now()
        else:
            job.status = ProcessingJob.Status.FAILED
            job.error_message = result.get('error', 'Unknown error')
            job.current_stage = f"Failed at: {result.get('stage_failed', 'unknown')}"

        job.save()

    except Exception as e:
        logger.exception(f"Job {job_id} processing thread crashed: {e}")
        try:
            ProcessingJob.objects.filter(id=job_id).update(
                status=ProcessingJob.Status.FAILED,
                error_message=f"Internal error: {str(e)}",
            )
        except Exception:
            pass
