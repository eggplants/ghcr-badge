max_requests = 1200
preload_app = True
timeout = 5
# import multiprocessing
# workers = multiprocessing.cpu_count() * 2 + 1
wsgi_app = "ghcr_badge.server:app"
