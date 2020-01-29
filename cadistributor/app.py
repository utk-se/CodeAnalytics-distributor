
import flask
from flask import request
from flask_httpauth import HTTPDigestAuth

app = flask.Flask(__name__)
auth = HTTPDigestAuth()

@app.route('/')
def index():
    return 'Ohello'

@app.route('/status', methods=['GET'])
def statuspage():
    '''Frontend for seeing activity of the requesters'''
    return 'Doing nothing.'

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
    return 'Not implemented'

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
