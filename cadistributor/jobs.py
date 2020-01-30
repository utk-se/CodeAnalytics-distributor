
from . import log
import pymongo
from pymongo.mongo_client import MongoClient
import bson, json
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
clientcollection = db.get_collection('clients')

def get_job_by_id(objectid):
    try:
        result = jobcollection.find_one({
            "_id": ObjectId(objectid)
        })
        # log.info(str(result))
        return dumps(result)
    except bson.errors.InvalidId as e:
        log.warn("InvalidId: " + str(objectid))
        return 406 # "Not Acceptable"

def get_unclaimed_job():
    result = jobcollection.find_one({
        "status": "unclaimed"
    })
