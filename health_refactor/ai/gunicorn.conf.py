"""Gunicorn settings for production (Docker / Render)."""
import multiprocessing
import os

port = os.getenv("PORT", os.getenv("APP_PORT", "8001"))
bind = f"0.0.0.0:{port}"

worker_class = "uvicorn.workers.UvicornWorker"
workers = int(
    os.getenv(
        "WEB_CONCURRENCY",
        os.getenv("GUNICORN_WORKERS", str(max(2, multiprocessing.cpu_count()))),
    )
)
threads = 1

timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

preload_app = False

proc_name = "product-dashboard-ai"
