#!/usr/bin/env python

import argparse, datetime, json, os, time
import requests, toml
import pygit2 as git
from requests.auth import HTTPBasicAuth
from . import log

config = {}

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
        return r.json()
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
        "lastcheckin": now.isoformat(),
        "lastcheckin_human": now.strftime('%F %T %z')
    }
    newdata.update(state)
    data.update(newdata)
    r = requests.put(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
        json=data,
        auth=config["auth"]
    )
    if r.status_code == requests.codes.unauthorized:
        log.err(r)
        raise ConnectionRefusedError("checkin: 401")
    if r.status_code == requests.codes.bad_request:
        log.err(r)
        raise RuntimeError("bad request")
    # log.debug(f"Checkin completed: {r.json()}")
    log.debug(f"Checkin completed: {status}")

def claim_job():
    r = requests.get(
        config["api"]["baseuri"] + "/jobs/claim_next",
        auth=config["auth"]
    )
    if r.status_code == requests.codes.ok:
        log.info("Claimed job successfully.")
    elif r.status_code == requests.codes.not_modified:
        log.warn("Job was already claimed by this worker, reclaimed.")
    else:
        log.error("Failed to claim job:", job._id)
        raise RuntimeError("Job Claim Fail")
    checkin(
        "claimed job",
        {"job": {
            "_id": job["_id"],
            "url": job["url"]
        }}
    )
    return r.json()

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

    checkin("analyze", {
        "job": {
            "_id": job["_id"],
            "url": job["url"],
            "workdir": workdir,
            "repodir": repodir
        }
    })

    # TODO run analysis_program <jobdir>

    # TODO fetch and return json from result_file

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
    except KeyError as e:
        log.error("Config missing value!")
        log.error(e)
        raise e
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)
        raise e

    log.info("Pinging API...")
    ping_master()

    log.info("Worker: " + config["api"]["workername"])

    log.info("Checking in...")
    checkin("bootup", {
        "endpoint": config["api"]["baseuri"]
    })

    try:
        main_loop()
    except KeyboardInterrupt as e:
        log.warn("Stopping from SIGINT...")
        checkin("stopped")
    except Exception as e:
        log.err(f"Unknown exception: {e}")
        checkin("error",{
            "error": {
                "type": str(type(e)),
                "str": str(e),
                "time": datetime.datetime.utcnow().isoformat()
            }
        })
        raise e

    checkin("exited")


def main_loop():
    # TODO check if previous job was finished,
    # if not: get that job and run it

    while True:
        log.debug("main_loop")
        checkin("sleeping")
        time.sleep(5)

        try:
            job = claim_job()
            if job is not None:
                log.info(f"Claimed job: {job['_id']}, going to work.")
                run_job(job)
        except RuntimeError as e:
            log.warn("Failed to claim job, continuing main loop.")
            log.err(e)


if __name__ == "__main__":
    __main__()
