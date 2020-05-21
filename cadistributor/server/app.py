
import secrets
import subprocess
import flask
import urllib
from . import db
from .. import log
from ..utils import *
from bson.json_util import loads, dumps
from flask import request
from flask_httpauth import HTTPBasicAuth

app = flask.Flask(__name__)
auth = HTTPBasicAuth()

### service helpers

def json_response(data, code, pretty = False):
    response = app.response_class(
        response=dumps(data, indent=2, sort_keys=True) if pretty else dumps(data),
        status=code,
        mimetype='application/json'
    )
    return response

@app.errorhandler(CodeAnalyticsError)
def handle_ValueError(e):
    response = app.response_class(
        response=e.message,
    )
    response.status_code = e.status_code
    return response

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
    token = db.get_worker_token(clientid)
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
    Apply headers to served response.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# automatically pulls updates I make
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
    state = db.get_worker_state(workerid)
    return json_response(state, 200, True)

@app.route('/status/worker/<workerid>', methods=['PUT'])
@auth.login_required
def update_worker_status(workerid):
    if auth.username() != workerid:
        return 'Not allowed.', 403 # known fobidden
    data = loads(request.data)
    if data is None:
        return 400
    log.debug(f"worker {workerid} status: {data['status']} ")
    newstate = db.update_worker_state(workerid, data)
    return json_response(newstate, 200)

### /repo/

@app.route('/repo/<url>', methods=['GET'])
@auth.login_required
def get_repo(url):
    url = urllib.parse.unquote_plus(url)
    result = db.get_repo(url)
    return json_response(result, 200 if result else 404, True)

@app.route('/repo/<url>', methods=['PUT'])
@auth.login_required
def put_repo(url):
    url = urllib.parse.unquote_plus(url)
    data = loads(request.data)
    if data is None:
        raise CodeAnalyticsError("Must supply initial object data!", 400)
    data.update({
        "frames": {}
    })
    return 'TODO', 501 # TODO not implemented

@app.route('/repo/<url>/frame/<version>', methods=['PUT', 'POST'])
@auth.login_required
def put_repo_frame(url, version):
    ensureVersionStringMongoSafe(version)
    url = urllib.parse.unquote_plus(url)
    data = loads(request.data)
    if data is None:
        raise CodeAnalyticsError("No valid data supplied.", 400)
    return 'TODO', 501 # TODO not implemented

@app.route('/repo/<url>/frame/<version>', methods=['GET'])
@auth.login_required
def get_repo_frame(repo, version):
    ensureVersionStringMongoSafe(version)
    url = urllib.parse.unquote_plus(url)
    return 'TODO', 501 # TODO not implemented

### /jobs/

### /jobs/frame/

# give a worker a job for creating a frame of a specific version
@app.route('/jobs/frame/<version>/claim', methods=['GET'])
@auth.login_required
def claim_frame_job(version):
    workername = auth.username()
    ensureVersionStringMongoSafe(version)
    repo = db.claim_repo_job_by_frame_version(version, workername)
    return json_response(repo, 201 if repo else 204, True) # created / no-content

@app.route('/jobs/frame/<version>/complete/<url>', methods=['PUT', 'POST'])
@auth.login_required
def complete_frame_job(version, url):
    ensureVersionStringMongoSafe(version)
    url = urllib.parse.unquote_plus(url)
    return 'TODO', 501 # TODO not implemented

### end routes

log.info("App import done.")
