from django.contrib import admin
from .models import ProcessingJob

@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'status', 'progress_percent',
                    'duration_formatted', 'elapsed_seconds', 'created_at']
    list_filter = ['status']
    search_fields = ['original_filename', 'id']
    readonly_fields = ['id', 'created_at', 'completed_at', 'processing_log', 'methods_used']
    ordering = ['-created_at']
