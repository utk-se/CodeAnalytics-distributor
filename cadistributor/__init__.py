#!/usr/bin/env python3

"""CA Distributor

Includes job server and worker that will distribute generic json/bson job items.

cadistributor.server.app:app should be run with a flask server. (like gunicorn)

cadistributor.worker contains worker programs that can be run via their module:
$ python -m cadistributor.worker.jsonresults
"""

__version__ = "0.1.1"
