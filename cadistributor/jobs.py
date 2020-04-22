
from . import log
import pymongo
from pymongo.mongo_client import MongoClient
import bson, json, datetime
from bson.objectid import ObjectId
from bson.json_util import loads, dumps


jobtemplate = {
    "url" : None,
    "name" : None,
    "target_commit" : None,
    "target_commit_date" : None,
    "status" : "unclaimed",
    "worker" : None,
    "source" : None
}

dbclient = MongoClient()
db = dbclient.get_database(name='ca-core')
jobcollection = db.get_collection('jobs')
workercollection = db.get_collection('workers')

### workercollection

def get_worker_state(workername):
    try:
        result = workercollection.find_one({
            "name": workername
        })
        if result is None:
            return 404
        return result["state"]
    except Exception as e:
        log.err(e)
        raise e

def get_worker_token(workername):
    try:
        result = workercollection.find_one({
            "name": workername
        })
        if result is None:
            return None # unauthorized
        return result["token"]
    except Exception as e:
        log.err(e)
        return None

def update_worker_state(workername, state):
    try:
        worker = workercollection.find_one_and_update({
            "name": workername
        }, {"$set": {
            "state": state,
            "changed": datetime.datetime.utcnow()
        }}, return_document=pymongo.ReturnDocument.AFTER)
        if worker is None:
            return 404
        return worker["state"]
    except Exception as e:
        log.err(e)
        raise e

### jobcollection

def get_job_by_id(objectid):
    try:
        result = jobcollection.find_one({
            "_id": ObjectId(objectid)
        })
        # log.info(str(result))
        return result
    except bson.errors.InvalidId as e:
        log.warn("InvalidId: " + str(objectid))
        return 406 # "Not Acceptable"

def get_unclaimed_job():
    result = jobcollection.find_one({
        "status": "unclaimed"
    })
    if result is None:
        return None
    return result

def claim_job(job, claimer):
    job["status"] = "claimed"
    job["claim"] = {}
    job["claim"]["worker"] = claimer
    job["claim"]["time"] = datetime.datetime.utcnow()
    replacement = jobcollection.replace_one({
        "_id": job["_id"],
        "status": "unclaimed"
    }, job)
    if replacement.modified_count == 0:
        return 503
    log.info(f"{claimer} claimed job {job['_id']}")
    return job

def claim_next_job(workername):
    try:
        job = get_unclaimed_job()
        if job is None:
            return None
        job = claim_job(job, workername)
        return job
    except Exception as e:
        log.err(e)
        return None

def add_result_to_job(jobid, version, result):
    job = get_job_by_id(jobid)
    if job.get("results", None) is None:
        job["results"] = {}
    job["results"][version] = result
    replacement = jobcollection.replace_one({
        "_id": job["_id"],
    }, job)
    if replacement.modified_count == 0:
        log.err("Failed to save result to job!")
        log.warn("Zero documents modified by replacement.")
        raise RuntimeWarning(f"No documents updated during job {jobid} result submission.")
    else:
        log.info(f"Job {jobid} result {version} stored.")
