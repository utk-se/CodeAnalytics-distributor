
"""
NOTE: expects access to the WoC mongodb on local 27018,
and ca-core on local machine

SSH forward the da1 server to localhost:27018
"""

import argparse
import pymongo
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps

from .. import log
from ..utils import *
from ..server import db

da1_dbclient = MongoClient('localhost', 27018)
output_db = db.db
gh_db = da1_dbclient.get_database(name="gh202003")

da1_gh_repos = gh_db.get_collection("repos")

output_collection = output_db.get_collection("repos_v1")

status = {
    "n": 0
}

def insert_url_from_repoitem(repoitem):
    status["n"] = status["n"] + 1

    url = f"https://github.com/{repoitem['nameWithOwner']}.git"

    try:
        output_collection.insert_one({"url": url})
    except pymongo.errors.DuplicateKeyError as e:
        log.debug(f"ignoring duplicate item: {url} ({e})")

    if status["n"] % 1000 == 0:
        log.info(f"{status['n'] // 1000}k repos inserted ...")


def insert_all_urls():
    cursor = da1_gh_repos.find()
    cursor.batch_size(2000)

    for i in cursor:
        # log.debug(i)
        insert_url_from_repoitem(i)

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

    insert_all_urls()
