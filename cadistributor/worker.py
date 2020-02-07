
import argparse, datetime, json
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

def get_worker_status():
    r = requests.get(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
    )
    if r.ok:
        return r.json()
    elif r.status_code == requests.codes.unauthorized:
        raise ConnectionRefusedError("unauthorized")

def checkin(status: str = "nothing", state: dict = {}):
    now = datetime.datetime.now(datetime.timezone.utc)
    newdata={
        "status": status,
        "lastcheckin": now.isoformat(),
        "lastcheckin_human": now.strftime('%F %T %z')
    }
    newdata.update(state)
    # log.debug(newdata)
    r = requests.put(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
        json=newdata,
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
        {"jobid": job._id}
    )

def run_job(job):
    checkin(
        "running",
        {"jobid": job._id}
    )

    # TODO make dirs:
    # tempdir
    # jobdir

    # TODO clone repo inside tempdir
    # into jobdirpattern

    # TODO cd into tempdir,

    # TODO run analysis_program <jobdir>

    # TODO fetch and return json from result_file

    checkin("finished")


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
        assert config["analysis"]["tempdir"] is not None
        config["auth"] = HTTPBasicAuth(
            config["api"]["workername"],
            config["api"]["token"]
        )
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)

    log.info("Pinging API...")
    ping_master()

    log.info("Worker: " + config["api"]["workername"])

    log.info("Checking in...")
    checkin("bootup")


def main_loop():
    # TODO check if previous job was finished,
    # if not: get that job and run it

    while True:
        log.debug("main_loop")


if __name__ == "__main__":
    # TODO catch
    try:
        __main__()
    except KeyboardInterrupt as e:
        log.warn("Stopping from SIGINT...")
        checkin("stopped")
