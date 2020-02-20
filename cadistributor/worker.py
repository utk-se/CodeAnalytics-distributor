#!/usr/bin/env python

import argparse, datetime, json, os, time
import importlib
import requests, toml
from bson import json_util
from bson.json_util import loads, dumps
import pygit2 as git
from requests.auth import HTTPBasicAuth
from . import log

config = {}

class JobClaimFail(RuntimeError):
    pass

def ping_master():
    r = requests.get(
        config["api"]["baseuri"] + "/status"
    )
    log.debug(r)
    log.debug(r.content)

def get_worker_state():
    r = requests.get(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
    )
    if r.ok:
        return loads(r.text)
    elif r.status_code == requests.codes.unauthorized:
        raise ConnectionRefusedError("unauthorized")
    elif r.status_code == requests.codes.not_found:
        raise RuntimeError(f"Worker status for \'{config['api']['workername']}\' not found on server!")
    else:
        log.error(f"Unknown response: {r.status_code}")
        raise RuntimeError(f"Unknown response: {r.status_code}")

def checkin(status: str = "nothing", state: dict = {}):
    now = datetime.datetime.utcnow()
    data = get_worker_state() or {}
    newdata={
        "status": status,
        "lastcheckin": now,
        "lastcheckin_human": now.strftime('%F %T %z')
    }
    newdata.update(state)
    data.update(newdata)
    # log.debug(f"Putting data: {dumps(data)}")
    r = requests.put(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
        data=dumps(data),
        auth=config["auth"],
        headers={'Content-Type': 'application/json'}
    )
    if r.status_code == requests.codes.unauthorized:
        log.err(r)
        raise ConnectionRefusedError("checkin: 401")
    if r.status_code == requests.codes.bad_request:
        log.err(r)
        raise RuntimeError("bad request")
    # log.debug(f"Checkin completed: {r.json()}")
    log.info(f"Checkin completed: {status}")

def claim_job():
    r = requests.get(
        config["api"]["baseuri"] + "/jobs/claim_next",
        auth=config["auth"]
    )
    if r.status_code == requests.codes.ok:
        log.info("Claimed job successfully.")
    elif r.status_code == requests.codes.not_modified:
        log.warn("Job was already claimed by this worker, reclaimed.")
    elif r.status_code == requests.codes.no_content:
        log.debug("No jobs available.")
        return None
    else:
        log.error("Failed to claim job.")
        log.error(r.status_code)
        log.error(r.content)
        raise JobClaimFail()
    job = loads(r.text)
    checkin(
        "claimed job",
        {"job": {
            "_id": job["_id"],
            "url": job["url"]
        }}
    )
    return job

def run_job(job):
    checkin("setup", {
        "job": {
            "_id": job["_id"],
            "url": job["url"]
        }
    })

    # make all dirs:
    workdir = config["job"]["workdir"] % config["api"]["workername"]
    os.makedirs(workdir, mode=0o750, exist_ok=True)
    os.chdir(workdir)
    log.debug(f"Working in {workdir}")
    repodir = config["job"]["repodir"] % job["_id"]
    os.makedirs(repodir)

    # clone repo inside tempdir
    # into repodir
    checkin("clone", {
        "job": {
            "_id": job["_id"],
            "url": job["url"],
            "workdir": workdir,
            "repodir": repodir
        }
    })
    log.info(f"Beginning clone for job {job['_id']}")
    git.clone_repository(
        job["url"],
        repodir
    )

    funcname = config['analysis']['function'].__module__ + ":" + config['analysis']['function'].__name__
    log.debug(f"Using analysis_function: {funcname}")
    checkin("analyze", {
        "job": {
            "_id": job["_id"],
            "url": job["url"],
            "workdir": workdir,
            "repodir": repodir,
            "function": funcname
        }
    })

    # run analysis_program for <repodir>
    try:
        result = config['analysis']['function'](repodir)
        result['version'] = config['analysis']['module'].__version__
        assert result['version'] is not None
    except AssertionError as e:
        log.err("Result from analyzer malformed.")
        raise e
    except Exception as e:
        log.err("Unknown exception when calling the analysis_function!")
        raise e # will let the main loop report error to server

    # return result to server
    r = requests.put(
        config["api"]["baseuri"] + "/job/" + job["_id"].valueOf() + "/result/" + result['version'],
        data=dumps(result),
        auth=config["auth"],
        headers={'Content-Type': 'application/json'}
    )
    if not r.ok():
        log.err("Unknown error when submitting job result!")
        log.warn(r)
        log.debug(r.text)
        raise ConnectionError("Failed to communicate result to server.")

    checkin("completed")


def __main__():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Config file",
        required=True
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbosity increase"
    )

    args = parser.parse_args()
    if (args.verbose):
        log.setLevel(log.DEBUG)

    config.update(toml.load(args.config))
    try:
        assert config["api"]["baseuri"] is not None
        assert config["job"]["workdir"] is not None
        config["auth"] = HTTPBasicAuth(
            config["api"]["workername"],
            config["api"]["token"]
        )
        if not config["job"].get("repodir"):
            config["job"]["repodir"] = "job-%s"
        f_target = config["job"]["analysis_function"].rsplit(':', 1)
        config["analysis"] = {
            "module": f_target[0],
            "function": f_target[1]
        }
    except KeyError as e:
        log.error("Config missing value!")
        log.error(e)
        raise e
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)
        raise e

    log.info("Initializing analysis_function...")
    try:
        target_func_module = importlib.import_module(config["analysis"]["module"])
        config["analysis"]["module"] = target_func_module
    except ImportError as e:
        log.err(f"Could not import analysis_function module: {config['analysis']['module']}")
        log.err(e)
        raise e

    if config["analysis"]["function"] not in config["analysis"]["module"].__dict__:
        log.err(f"Could not find analysis_function {config['analysis']['function']} in module {config['analysis']['module'].__name__}.")
        raise ValueError(f"analysis_function \"{config['analysis']['function']}\" not in module \"{config['analysis']['module'].__name__}\"")

    config["analysis"]["function"] = config["analysis"]["module"].__dict__[config["analysis"]["function"]]
    if type(config["analysis"]["function"]) != type(lambda x: x):
        log.err("analysis_function does not appear to be a function!")
        raise AssertionError(f"type({config['analysis']['function']}) is not {type(lambda x: x)}")

    log.info("Pinging API...")
    ping_master()

    log.info("Worker: " + config["api"]["workername"])

    log.info("Checking in...")
    checkin("bootup", {
        "endpoint": config["api"]["baseuri"]
    })

    try:
        main_loop()
        checkin("exited")
    except KeyboardInterrupt as e:
        log.warn("Stopping from SIGINT...")
        checkin("stopped")
    except Exception as e:
        log.err(f"Unknown exception: {e}")
        checkin("error",{
            "error": {
                "type": str(type(e)),
                "str": str(e),
                "time": datetime.datetime.utcnow()
            }
        })
        raise e


def main_loop():
    # TODO check if previous job was finished,
    # if not: get that job and run it

    while True:
        log.debug("main_loop")

        try:
            job = claim_job()
            if job is not None:
                log.info(f"Claimed job: {job['_id']}, going to work.")
                run_job(job)
        except JobClaimFail as e:
            log.warn("Failed to claim job, continuing main loop.")
            log.err(e)

        checkin("sleeping")
        time.sleep(5)


if __name__ == "__main__":
    __main__()
