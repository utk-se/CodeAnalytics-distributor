
import argparse
import pymongo
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps

from multiprocessing.dummy import Pool as ThreadPool

from .. import log
from ..utils import *
from ..server import db

woc_dbclient = MongoClient('localhost', 27018)
woc_db = woc_dbclient.get_database(name='WoC')

proj_metadata_q1 = woc_db.get_collection("proj_metadata.Q")

woc_xfer = db.db.get_collection("woc_xfer")

mappings = {
    " =>": ":",
    "'": "\"",
    "NULL": '"total_files": 0',

    "total_c_or_c++_files": "c,cpp",
    "total_java_files": "java",
    "total_javascript_files": "javascript",
    "total_python_files": "python",
    "total_php_files": "php",
    "total_perl_files": "perl",
    "total_lua_files": "lua",
    "total_other_files": "other",
    # "total_files": ""
}

status = {
    "n": 0
}

def insert_translated_woc_item(srcitem):
    status["n"] = status["n"] + 1

    filecntstr = srcitem['fileInfo']
    for k, v in mappings.items():
        filecntstr = filecntstr.replace(k, v)

    parsedfilecnt = {}
    try:
        parsedfilecnt = loads(filecntstr)
    except Exception as e:
        log.err(e)

    srcitem['fileInfo'] = parsedfilecnt

    try:
        woc_xfer.insert_one(srcitem)
    except pymongo.errors.DuplicateKeyError as e:
        log.debug(f"ignoring duplicate item: {srcitem['projectID']}")

    if status["n"] % 1000 == 0:
        log.info(f"{status['n'] // 1000}k repos transferred...")

def translate_all_proj_metadata():
    n = 0
    source_items = proj_metadata_q1.find()

    source_items.batch_size(2000)
    for srcitem in source_items:
        insert_translated_woc_item(srcitem)

    log.info("Completed translate_all_proj_metadata")

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


    translate_all_proj_metadata()
