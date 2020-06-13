
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

# woc_projects = woc_db.get_collection("projects")
da1_gh_repos = gh_db.get_collection("repos")

output_collection = output_db.get_collection("gh_api")

status = {
    "n": 0
}

def insert_with_gh_api_response(repoitem):
    status["n"] = status["n"] + 1

    url = f"https://github.com/{repoitem['nameWithOwner']}.git"

    # check if output_collection already has item:
    if output_collection.find_one({"url": url}) is not None:
        log.debug(f"{url} already in collection!")
        return

    log.debug(f"getting {url}")

    # TODO

    repoitem["url"] = f"https://github.com/{repoitem['nameWithOwner']}.git"

    try:
        output_collection.insert_one(repoitem)
    except pymongo.errors.DuplicateKeyError as e:
        log.debug(f"ignoring duplicate item: {url} / {repoitem['_id']}")

    if status["n"] % 1000 == 0:
        log.info(f"{status['n'] // 1000}k repos completed...")


def fetch_all_api_data():
    cursor = da1_gh_repos.find()
    # cursor.batch_size(2000)

    for i in cursor:
        insert_with_gh_api_response(i)

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


    fetch_all_api_data()
