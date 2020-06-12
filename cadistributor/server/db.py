
from .. import log
import pymongo
from pymongo.mongo_client import MongoClient
import bson
import json
import datetime
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
from ..utils import *

templates = {
    "repo": {
        "url": None,  # unique key
        "result": {
            "0_0_0": {  # example, does not exist until inserted
                "status": "claimed",
                "worker": "ca-do-w1",
                # "gridfs_id": None
            }
        }
    },
    "result": {
        "url": "repo-url",
        "version": "0_0_0",
        "data": None # returned json from analyzer
    }
}

dbclient = MongoClient()
db = dbclient.get_database(name='ca-core')
workercollection = db.get_collection("workers")
repocollection = db.get_collection("repos_v1")
resultcollection = db.get_collection("results_v1")

# workercollection

def get_worker_state(workername):
    result = workercollection.find_one({
        "name": workername
    })
    if result is None:
        raise CodeAnalyticsError(f"no such worker: {workername}", 404)
    return result["state"]

def get_worker_token(workername):
    try:
        result = workercollection.find_one({
            "name": workername
        })
        if result is None:
            return None  # unauthorized
        return result["token"]
    except Exception as e:
        log.err(e)
        return None

def update_worker_state(workername, state):
    worker = workercollection.find_one_and_update({
        "name": workername
    }, {"$set": {
        "state": state,
        "changed": datetime.datetime.utcnow()
    }}, return_document=pymongo.ReturnDocument.AFTER)
    if worker is None:
        raise CodeAnalyticsError(f"worker {workername} not found", 404)
    return worker["state"]

# repocollection

def get_repo(url):
    try:
        result = repocollection.find_one({
            "url": url
        })
        return result
    except Err as e:
        log.warn(f"Could not find repo with url: {url}")
        return None

def claim_repo_job_by_result_version(version, workerid):
    try:
        log.debug(f"Job claim attempt v{version} for {workerid}...")
        target = repocollection.find_one_and_update(
            {
                f"result.{version}": {"$exists": False}
            },
            {
                "$set": {
                    f"result.{version}": {
                        "status": "claimed",
                        "worker": workerid
                    }
                }
            },
            return_document=pymongo.ReturnDocument.AFTER
        )
        return target
    except Exception as e:
        log.err("Failure claiming job...")
        raise e

# resultcollection

def store_json_result(version, repo_url, workerid, data):
    try:
        log.info(f"Storing result v{version} from {workerid} ...")
        r = resultcollection.insert_one({
            "version": version,
            "repo": repo_url,
            "worker": workerid,
            "servertime": datetime.datetime.utcnow(),
            "data": data
        })
        # TODO is there any way to check the insertion?
    except Exception as e:
        log.err("Failed to store result into db...")
        raise e

def find_results(version, repo_url):
    try:
        r = resultcollection.find({
            "version": version,
            "repo": repo_url
        })
        return r
    except Exception as e:
        log.err("Failed searching for results in the db!")
        log.err(str(e))
