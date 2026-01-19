from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# API Metrics
api_requests_total = Counter(
    'vivacampo_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'vivacampo_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Job Metrics
active_jobs = Gauge(
    'vivacampo_active_jobs',
    'Number of active jobs',
    ['job_type', 'tenant_id']
)

job_processing_duration = Histogram(
    'vivacampo_job_processing_duration_seconds',
    'Job processing duration in seconds',
    ['job_type']
)

job_failures_total = Counter(
    'vivacampo_job_failures_total',
    'Total job failures',
    ['job_type', 'error_type']
)


def get_metrics():
    """
    Return Prometheus metrics in text format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
