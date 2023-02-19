"""Gunicorn configuraitons."""

max_requests = 1200
preload_app = True
timeout = 5
wsgi_app = "ghcr_badge.server:app"
