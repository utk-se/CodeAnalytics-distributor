
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
woc_db = da1_dbclient.get_database(name='WoC')
gh_db = da1_dbclient.get_database(name="gh202003")

# woc_projects = woc_db.get_collection("projects")
da1_gh_repos = gh_db.get_collection("repos")
proj_metadata_q1 = woc_db.get_collection("proj_metadata.Q")

woc_xfer = db.db.get_collection("woc_xfer")

mappings = {
    " =>": ":",
    "'": "\"",
    "NULL": '"total_files": 0',

    "total_": "",
    "_files": "",

    "c_or_c++": "c,cpp",
}

status = {
    "n": 0
}

def insert_with_filetypes(repoitem):
    status["n"] = status["n"] + 1

    projID = repoitem['nameWithOwner'].replace('/', '_')

    log.debug(f"searching for {projID}")
    srcitem = proj_metadata_q1.find_one({"projectID": projID})
    if srcitem is None:
        log.debug(f"{projID} not found")

    filecntstr = srcitem['fileInfo']
    for k, v in mappings.items():
        filecntstr = filecntstr.replace(k, v)

    parsedfilecnt = {}
    try:
        parsedfilecnt = loads(filecntstr)
    except Exception as e:
        log.err(e)

    repoitem["files"] = parsedfilecnt
    repoitem["metadataItem"] = srcitem
    repoitem["url"] = f"https://github.com/{repoitem['nameWithOwner']}.git"

    try:
        woc_xfer.insert_one(repoitem)
    except pymongo.errors.DuplicateKeyError as e:
        log.debug(f"ignoring duplicate item: {projID} / {repoitem['_id']}")

    if status["n"] % 1000 == 0:
        log.info(f"{status['n'] // 1000}k repos transferred...")


def merge_repos_with_files():
    cursor = da1_gh_repos.find()
    # cursor.batch_size(2000)

    for i in cursor:
        # log.debug(i)
        insert_with_filetypes(i)

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


    merge_repos_with_files()
