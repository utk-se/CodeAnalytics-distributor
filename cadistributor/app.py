
import secrets
import flask
from . import log, jobs
from bson.json_util import loads, dumps
from flask import request
from flask_httpauth import HTTPBasicAuth

app = flask.Flask(__name__)
auth = HTTPBasicAuth()

log.setLevel(log.DEBUG)
log.info("Setting up app...")

log.info("Getting SESSIONKEY...")
try:
    f = open('secrets/sessionkey', 'rb')
    key = f.read() # bytes
    f.close()
    if len(key) <= 8:
        raise ValueError("Not enough bytes in sessionkey")
    app.config["SECRET_KEY"] = key
except FileNotFoundError as e:
    log.warn("Creating new sessionkey")
    key = secrets.token_bytes(16)
    f = open('secrets/sessionkey', 'wb+')
    f.write(key)
    f.close()
    app.config["SECRET_KEY"] = key
except Exception as e:
    log.crit("Failed to get a Flask sessionkey")
    raise e

@auth.get_password
def get_client_token(clientid):
    token = jobs.get_worker_token(clientid)
    if type(token) is not str:
        if token == 401: # unauthorized
            log.debug("No token for client", clientid)
            return None
        raise ValueError(token)
    else:
        return token

@app.route('/', methods=['GET'])
def index():
    return 'Hi. If you don\'t know what this is, you probably shouldn\'t be here.'

@app.route('/', methods=['POST', 'PUT'])
def indexdata():
    log.debug(request.get_json())
    return request.get_json()

@app.after_request
def add_header(r):
    """
    Force no caching.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

### /status/

@app.route('/status', methods=['GET'])
def statuspage():
    '''Frontend for seeing activity of the requesters'''
    return 'Seems ok from here.'

@app.route('/status/worker/<workerid>', methods=['GET'])
def get_worker_status(workerid):
    status, state = jobs.get_worker_status(workerid)
    return {"status": status, "state": state}, 200

@app.route('/status/worker/<workerid>', methods=['PUT'])
@auth.login_required
def update_worker_status(workerid):
    if auth.username() != workerid:
        return 'Not allowed.', 403
    data = request.get_json(force=True)
    if data is None:
        return 400
    log.debug("worker" + workerid + "update", data)
    jobs.update_worker_status(
        workerid,
        data["status"],
        data
    )
    newstatus = jobs.get_worker_status(workerid)
    return newstatus[1], 200

### /jobs/

@app.route('/jobs/next', methods=['GET'])
@auth.login_required
def get_next_job():
    '''Return a job that hasn't been claimed yet.'''
    result = jobs.get_unclaimed_job()
    if result is None:
        return "No unclaimed job found.", 204 # no content
    return result

@app.route('/jobs/claim_next', methods=['GET'])
@auth.login_required
def claim_next_job():
    workername = auth.username()
    result = jobs.claim_next_job(workername)
    if result is None:
        return "No unclaimed job found.", 204
    elif result is 503:
        return "Job claimed by other, try again.", 503
    else:
        return result

@app.route('/jobs/list', methods=['GET'])
@auth.login_required
def list_jobs():
    return 'Not implemented'

@app.route('/jobs/add', methods=['POST'])
@auth.login_required
def add_job():
    return 'Not implemented'

@app.route('/jobs/remove', methods=['POST'])
@auth.login_required
def remove_job():
    return 'Not implemented'

@app.route('/jobs/<jobid>', methods=['GET'])
@auth.login_required
def get_job(jobid):
    '''Return the full job object'''
    result = jobs.get_job_by_id(jobid)
    if type(result) is int:
        return "No such job: " + jobid, result
    elif result is None:
        return "Could not find that job.", 404
    elif result:
        return result, 200

@app.route('/jobs/<jobid>', methods=['PUT'])
@auth.login_required
def write_job_data(jobid):
    '''Overwrites the job object'''
    return 'Not implemented'

@app.route('/jobs/claim/<jobid>', methods=['POST'])
@auth.login_required
def claim_job(jobid):
    """Reject if the job is already claimed."""
    return 'Not implemented' # TODO

@app.route('/jobs/<jobid>', methods=['PATCH'])
@auth.login_required
def update_job(jobid):
    '''Modifies the job object'''
    return 'Not implemented'

@app.route('/jobs/<jobid>', methods=['DELETE'])
@auth.login_required
def delete_job(jobid):
    '''Yep.'''
    return 'Not implemented'

log.info("App import done.")
