
reload = True
pidfile = "gunicorn.pid"
bind = ['127.0.0.1:8000', 'unix:ca-core.sock', '[::1]:8000']
worker_class = "gthread"
workers = 4

def on_reload(server):
    pass

def when_ready(server):
    pass

def on_exit(server):
    pass
