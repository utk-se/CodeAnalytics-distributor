
import argparse, datetime
import requests, toml
from requests.auth import HTTPDigestAuth
from . import log

config = {}

def ping_master():
    r = requests.get(
        config["api"]["baseuri"] + "/status"
    )
    log.debug(r)
    log.debug(r.content)

def checkin(state: str = "nothing", extra_status_data: dict = {}):
    now = datetime.datetime.now(datetime.timezone.utc)
    newdata={
        "state": state,
        "lastcheckin": now.isoformat(),
        "lastcheckin_human": now.strftime('%F %T %z')
    }
    newdata.update(extra_status_data)
    r = requests.put(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
        data=newdata,
        auth=config["auth"]
    )
    if r.status_code == requests.codes.unauthorized:
        log.error(r)
        raise ConnectionRefusedError("checkin: 401")
    log.debug(r)
    log.debug(r.json())

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
        "running job",
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
    #
    checkin("finished job")


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
        config["auth"] = HTTPDigestAuth(
            config["api"]["workername"],
            config["api"]["token"]
        )
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)

    log.info("Pinging API...")
    ping_master()

    log.info("Checking in...")
    checkin()


if __name__ == "__main__":
    __main__()
