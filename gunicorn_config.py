"""
Gunicorn configuration file for BOTA Project
Production-ready settings
"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Restart workers after this many requests to prevent memory leaks
graceful_timeout = 30
preload_app = False

# Logging
accesslog = "/home/bota/BOTA_Project/logs/gunicorn_access.log"
errorlog = "/home/bota/BOTA_Project/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "bota_gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/bota/BOTA_Project/gunicorn.pid"
user = "bota"
group = "bota"
tmp_upload_dir = None

# SSL (if needed, but usually handled by Nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Gunicorn server")

def on_reload(server):
    """Called to recycle workers during a reload."""
    print("Reloading Gunicorn server")

def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Spawning workers")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down Gunicorn server")
