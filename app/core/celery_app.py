# app/core/celery_app.py
import ssl
from celery import Celery
from app.core.config import REDIS_URL

celery_app = Celery("sharktank", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    # 👇 ensure the worker imports your tasks module on startup
    imports=("app.background.tasks",),

    task_routes={"app.background.tasks.*": {"queue": "deck"}},
    task_time_limit=60 * 25,
    worker_send_task_events=True,
    task_send_sent_event=True,
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Upstash TLS
if REDIS_URL.startswith("rediss://"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
