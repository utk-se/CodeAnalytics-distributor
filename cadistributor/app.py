
import flask
from flask import request

app = flask.Flask(__name__)

@app.route('/')
def index():
    return 'Ohello'

@app.route('/status', methods=['GET'])
def statuspage():
    return 'Doing nothing.'

@app.route('/jobs/retrieve')
def get_job():
    return 'Not implemented'

@app.route('/jobs/complete', methods=['PUT'])
def complete_job(jobid):
    return 'Not implemented'

@app.route('/jobs/list', methods=['GET'])
def list_jobs():
    return 'Not implemented'

@app.route('/jobs/add', methods=['PUT'])
def add_job():
    return 'Not implemented'

@app.route('/jobs/remove')
def remove_job():
    return 'Not implemented'

@app.route('/jobs/result/<jobid>', methods=['GET'])
def get_job_result(jobid):
    return 'Not implemented'
