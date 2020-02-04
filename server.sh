#!/bin/bash
source ./venv/bin/activate
gunicorn "cadistributor.app:app" -c gunicorn-config.py
