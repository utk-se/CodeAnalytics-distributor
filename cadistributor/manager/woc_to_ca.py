
"""
Inserts repos into the ca-core repos collection from the woc source.

seriously, don't run this on a home machine, performance is critical to
how quickly the db can be accessed
"""

import argparse
import pymongo
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps

from .. import log
from ..utils import *
from ..server import db


# def insert_carepo_from_wocrepo(item):

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbosity increase"
    )

    args = parser.parse_args()
    if (args.verbose):
        log.setLevel(log.DEBUG)
