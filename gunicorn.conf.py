import os

# gunicorn.conf.py
bind = os.getenv("GUNICORN_BIND", "unix:/home/micu/Micu_market/gunicorn.sock")
workers = 3
worker_class = "uvicorn_worker.UvicornWorker"  # ASGI worker (pachet uvicorn-worker; cel din uvicorn.workers e deprecat/incompatibil)
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 5
timeout = 120
graceful_timeout = 120
umask = 0o007
