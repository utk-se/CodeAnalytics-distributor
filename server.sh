#!/bin/bash
source ./venv/bin/activate
gunicorn "cadistributor.server.app:app" -c gunicorn-config.py
