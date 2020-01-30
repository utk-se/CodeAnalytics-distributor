
import secrets
import flask
from . import log, jobs
from flask import request
from flask_httpauth import HTTPDigestAuth

app = flask.Flask(__name__)
auth = HTTPDigestAuth()

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
    # TODO get token from db
    return 't'

@app.route('/')
def index():
    return 'Hi.'

### /status/

@app.route('/status', methods=['GET'])
def statuspage():
    '''Frontend for seeing activity of the requesters'''
    return 'Seems ok from here.'

@app.route('/status/worker/<workerid>', methods=['GET'])
def get_worker_status(workerid):
    return 'Probably doing work.'

### /jobs/

@app.route('/jobs/next', methods=['GET'])
@auth.login_required
def get_next_job():
    '''Return the id of a job that hasn't started yet.'''
    return 'No jobs yet.'

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
