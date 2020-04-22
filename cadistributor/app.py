
import secrets
import subprocess
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

@app.route('/')
def index():
    return 'Hi. If you don\'t know what this is, you probably shouldn\'t be here.', 418

@app.after_request
def add_header(r):
    """
    Force no caching.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@app.route('/githook', methods=['POST'])
def git_pull():
    data = request.get_json(force=True)
    log.info(f"githook on {data['ref']}")
    # log.info(f"headers: {request.headers}")
    try:
        if data["pusher"]["name"] == "robobenklein":
            proc = subprocess.run(
                ["git", "pull"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            if proc.returncode != 0:
                log.warn("git pull failed:")
                for line in proc.stdout.split('\n'):
                    log.warn(line)
            else:
                log.info("git pull success")
                return {"action": "pulled"}, 200
        return {"action": "none"}, 200
    except Exception as e:
        log.err(e)
        return {"action": "invalid"}, 400

### /status/

@app.route('/status', methods=['GET'])
def statuspage():
    '''Frontend for seeing activity of the requesters'''
    return 'Seems ok from here.', 200

@app.route('/status/worker/<workerid>', methods=['GET'])
def get_worker_status(workerid):
    state = jobs.get_worker_state(workerid)
    if type(state) == int:
        return str(state), state
    return dumps(state, indent=2, sort_keys=True), 200

@app.route('/status/worker/<workerid>', methods=['PUT'])
@auth.login_required
def update_worker_status(workerid):
    if auth.username() != workerid:
        return 'Not allowed.', 403
    data = loads(request.data)
    if data is None:
        return 400
    log.debug(f"worker {workerid} status: {data['status']} ")
    newstate = jobs.update_worker_state(workerid, data)
    if type(newstate) is int:
        return {"error": newstate}, newstate
    return dumps(newstate), 200

### /jobs/

@app.route('/jobs/next', methods=['GET'])
@auth.login_required
def get_next_job():
    '''Return a job that hasn't been claimed yet.'''
    result = jobs.get_unclaimed_job()
    if result is None:
        return "No unclaimed job found.", 204 # no content
    return dumps(result), 200

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
        return dumps(result), 200

@app.route('/jobs/list', methods=['GET'])
@auth.login_required
def list_jobs():
    return 'Not implemented'

@app.route('/jobs/add', methods=['POST'])
@auth.login_required
def add_job():
    return 'Not implemented'

@app.route('/jobs/<jobid>/remove', methods=['POST'])
@auth.login_required
def remove_job(jobid):
    return 'Not implemented', 405

@app.route('/jobs/<jobid>', methods=['GET'])
@auth.login_required
def get_job(jobid):
    '''Return the full job object'''
    result = jobs.get_job_by_id(jobid)
    if type(result) is int:
        return "Error getting job id: " + jobid, result
    elif result is None:
        return "Could not find that job.", 404
    elif result:
        return dumps(result), 200

@app.route('/jobs/<jobid>/result/<version>', methods=['PUT'])
@auth.login_required
def write_job_data(jobid, version):
    '''Adds results to a job'''
    data = loads(request.data)
    if data is None:
        return "No valid data supplied.", 400
    if version != data['version']:
        return "Data version does not match endpoint.", 400
    log.debug(f"Result version {version} submitted for job {jobid}")
    jobs.add_result_to_job(jobid, version, data)
    return "Data stored.", 201 # created

@app.route('/jobs/<jobid>', methods=['PATCH'])
@auth.login_required
def update_job(jobid):
    '''Modifies the job object'''
    return 'Not implemented', 405

@app.route('/jobs/<jobid>', methods=['DELETE'])
@auth.login_required
def delete_job(jobid):
    return 'Not allowed.', 405

log.info("App import done.")
