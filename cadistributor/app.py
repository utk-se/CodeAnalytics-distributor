
import flask
from flask import request

app = flask.Flask(__name__)

@app.route('/')
def index():
    return 'Ohello'

@app.route('/status', methods=['GET'])
def statuspage():
    '''Frontend for seeing activity of the requesters'''
    return 'Doing nothing.'

@app.route('/jobs/next', methods=['GET'])
def get_next_job():
    '''Return the id of a job that hasn't started yet.'''
    return 'No jobs yet.'

@app.route('/jobs/list', methods=['GET'])
def list_jobs():
    return 'Not implemented'

@app.route('/jobs/add', methods=['PUT'])
def add_job():
    return 'Not implemented'

@app.route('/jobs/remove', methods=['POST'])
def remove_job():
    return 'Not implemented'

@app.route('/jobs/<jobid>', methods=['GET'])
def get_job(jobid):
    '''Return the full job object'''
    return 'Not implemented'

@app.route('/jobs/<jobid>', methods=['PUT'])
def write_job_data(jobid):
    '''Overwrites the job object'''
    return 'Not implemented'

@app.route('/jobs/<jobid>', methods=['PATCH'])
def update_job(jobid):
    '''Modifies the job object'''
    return 'Not implemented'
