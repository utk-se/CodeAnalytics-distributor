
import argparse, datetime
import requests, toml
from . import log

config = {}

def ping_master():
    r = requests.get(
        config["api"]["baseuri"] + "/status"
    )
    log.debug(r)

def checkin():
    now = datetime.datetime.now(datetime.timezone.utc)
    r = requests.put(
        config["api"]["baseuri"] + "/status/worker/" + config["api"]["workername"],
        data={
            "lastcheckin": now.isoformat(),
            "lastcheckin_human": now.strftime('%F %T %z')
        },
        auth=(config["api"]["workername"], config["api"]["token"]),
    )
    log.debug(r)

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
    except AssertionError as e:
        log.error("Config check failed:")
        log.error(e)

    log.info("Pinging API...")
    ping_master()

    log.info("Checking in...")
    checkin()

def do_analysis(job):
    pass

    # TODO make dirs:
    # tempdir
    # jobdir

    # TODO clone repo inside tempdir
    # into jobdirpattern

    # TODO cd into tempdir,

    # TODO run analysis_program <jobdir>

    # TODO fetch and return json from result_file

if __name__ == "__main__":
    __main__()
