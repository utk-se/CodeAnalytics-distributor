
import argparse, datetime, json, os, time
import requests, toml
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
    else:
        log.error(f"Unknown response: {r.status_code}")
        raise RuntimeError(f"Unknown response: {r.status_code}")

def checkin(status: str = "nothing", state: dict = {}):
    now = datetime.datetime.utcnow()
    data = get_worker_state()
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
        log.error(r)
        raise ConnectionRefusedError("checkin: 401")
    if r.status_code == requests.codes.bad_request:
        log.err(r)
        raise RuntimeError("bad request")
    log.debug(f"Checkin completed: {r.json()}")

def claim_job(job):
    r = requests.post(
        config["api"]["baseuri"] + "/jobs/claim/" + job._id,
        data={
            "worker": config["api"]["workername"]
        },
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
    repodir = config["job"]["repodir"] % job["_id"]
    os.makedirs(repodir)

    checkin("clone", {
        "job": {
            "_id": job["_id"],
            "url": job["url"],
            "workdir": workdir,
            "repodir": repodir
        }
    })

    # TODO clone repo inside tempdir
    # into repodir

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
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)

    log.info("Pinging API...")
    ping_master()

    log.info("Worker: " + config["api"]["workername"])

    log.info("Checking in...")
    checkin("bootup", {
        "endpoint": config["api"]["baseuri"]
    })

    main_loop()

    checkin("exited")


def main_loop():
    # TODO check if previous job was finished,
    # if not: get that job and run it

    while True:
        log.debug("main_loop")
        checkin("sleeping")
        time.sleep(5)


if __name__ == "__main__":
    # TODO catch
    try:
        __main__()
    except KeyboardInterrupt as e:
        log.warn("Stopping from SIGINT...")
        checkin("stopped")
