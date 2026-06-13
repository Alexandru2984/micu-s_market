# gunicorn.conf.py
bind = "unix:/home/micu/Micu_market/gunicorn.sock"
workers = 3
worker_class = "uvicorn.workers.UvicornWorker"  # ASGI worker; păstrează compatibilitatea cu features async viitoare
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 5
timeout = 120
graceful_timeout = 120
