#!/usr/bin/env python3

"""CA Distributor

Includes job server and worker that will distribute generic json/bson job items.

cadistributor.worker can be run as a program. (__main__)

cadistributor.app:app should be run with a flask server. (like gunicorn)
"""

__version__ = "0.1.0"
