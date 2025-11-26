"""Konfiguration für Gunicorn"""

bind = "192.168.1.1:80"
worker_class = "eventlet"
workers = 1
