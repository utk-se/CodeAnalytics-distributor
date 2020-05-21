#!/usr/bin/env python

import argparse, datetime, json, os, time
import shutil
import importlib
import toml
from bson import json_util
from bson.json_util import loads, dumps
from requests.auth import HTTPBasicAuth
import pygit2 as git
from .. import log
from ..utils import *
from .api import *


class CodeAnalyticsFrameWorker(CodeAnalyticsWorker):
    def __init__(self, configfile):
        self.config = toml.load(configfile)
        try:
            assert self.config["api"]["baseuri"] is not None
            assert self.config["job"]["workdir"] is not None
            self.config["auth"] = HTTPBasicAuth(
                self.config["api"]["workername"],
                self.config["api"]["token"]
            )
            if not self.config["job"].get("repodir"):
                self.config["job"]["repodir"] = "job-%s"
            f_target = self.config["job"]["analysis_function"].rsplit(':', 1)
            self.config["analysis"] = {
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
            target_func_module = importlib.import_module(self.config["analysis"]["module"])
            self.config["analysis"]["module"] = target_func_module
            self.config["analysis"]["version"] = self.config['analysis']['module'].__version__
        except ImportError as e:
            log.err(f"Could not import analysis_function module: {self.config['analysis']['module']}")
            log.err(e)
            raise e

        if self.config["analysis"]["function"] not in self.config["analysis"]["module"].__dict__:
            log.err(f"Could not find analysis_function {self.config['analysis']['function']} in module {self.config['analysis']['module'].__name__}.")
            raise ValueError(f"analysis_function \"{self.config['analysis']['function']}\" not in module \"{self.config['analysis']['module'].__name__}\"")

        self.config["analysis"]["function"] = self.config["analysis"]["module"].__dict__[self.config["analysis"]["function"]]
        if type(self.config["analysis"]["function"]) != type(lambda x: x):
            log.err("analysis_function does not appear to be a function!")
            raise AssertionError(f"type({self.config['analysis']['function']}) is not {type(lambda x: x)}")

        log.info("Pinging API...")
        ping_master()

        log.info("Worker: " + self.config["api"]["workername"])

        log.info("Checking in...")
        self.checkin("bootup", {
            "endpoint": self.config["api"]["baseuri"]
        })

    def claim_job(self):
        version = self.config["analysis"]["version"]
        r = requests.get(
            self.config["api"]["baseuri"] + f"/jobs/frame/{version}/claim",
            auth=self.config["auth"]
        )
        if r.status_code == requests.codes.ok or r.status_code == requests.codes.created:
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
            raise JobClaimFail(r)
        job = loads(r.text)
        self.checkin(
            "claimed frame job",
            {"job": {
                "url": job["url"],
                "version": version
            }}
        )
        return job

    def execute_job(self, repo):
        self.checkin("setup", {
            "job": {
                "url": repo["url"]
            }
        })

        # make all dirs:
        workdir = self.config["job"]["workdir"] % self.config["api"]["workername"]
        os.makedirs(workdir, mode=0o750, exist_ok=True)
        os.chdir(workdir)
        log.debug(f"Working in {workdir}")
        repodir = self.config["job"]["repodir"] % escape_url(repo["url"])
        os.makedirs(repodir)
        log.debug(f"Repo dir: {repodir}")

        # clone repo inside tempdir
        # into repodir
        self.checkin("clone", {
            "job": {
                "url": repo["url"],
                "workdir": workdir,
                "repodir": repodir
            }
        })
        log.info(f"Beginning clone for job {repo['url']}")
        git.clone_repository(
            repo["url"],
            repodir
        )

        funcname = self.config['analysis']['function'].__module__ + ":" + self.config['analysis']['function'].__name__
        log.debug(f"Using analysis_function: {funcname}")
        frame_version = self.config["analysis"]["version"]
        self.checkin("analyze", {
            "job": {
                "url": repo["url"],
                "frame_version": frame_version,
                "workdir": workdir,
                "repodir": repodir,
                "function": funcname
            }
        })

        # run analysis_program for <repodir>
        try:
            result = self.config['analysis']['function'](repodir)
            # TODO assert dataframe is intact
        except AssertionError as e:
            log.err("Result from analyzer malformed.")
            raise e
        except Exception as e:
            log.err("Unknown exception when calling the analysis_function!")
            raise e # will let the main loop report error to server

        # return result to server
        endpoint = f"{self.config['api']['baseuri']}/jobs/frame/{frame_version}/complete/{escape_url(repo['url'])}"
        log.debug(f"Result submission endpoint: {endpoint}")
        # r = requests.put(
        #     endpoint,
        #     data=dumps(result),
        #     auth=self.config["auth"],
        #     headers={'Content-Type': 'application/json'}
        # )
        # TODO binary upload of dataframe (feather?) format
        if not r.status_code == requests.codes.created: # note: is @property, not function
            log.err("Unknown error when submitting job result!")
            log.warn(r)
            log.debug(r.text)
            raise ConnectionError("Failed to communicate result to server.")

        self.checkin("cleanup")

        reportRmFailure = lambda f, p, e: log.err(f"failed to remove {p}: {e}")
        shutil.rmtree(repodir, onerror=reportRmFailure)

        self.checkin("completed")

    def job_loop(self):
        # TODO bail out after N consecutive failures

        while True:
            log.debug("job_loop")

            try:
                repo = self.claim_frame_job(self.config["analysis"]["version"])
                if repo is not None:
                    log.info(f"Claimed job: {repo['url']}, going to work...")
                    self.run_job(repo)
                else:
                    self.checkin("sleeping")
                    time.sleep(5)
            except JobClaimFail as e:
                log.warn("Failed to claim job, continuing main loop.")
                log.err(e)
                self.checkin("claimfailed")
                time.sleep(10)

    def start(self):
        try:
            self.job_loop()
            self.checkin("exited")
        except KeyboardInterrupt as e:
            log.warn("Stopping from SIGINT...")
            self.checkin("stopped")
        except Exception as e:
            log.err(f"Unknown exception: {e}")
            self.checkin("error",{
                "error": {
                    "type": str(type(e)),
                    "str": str(e),
                    "time": datetime.datetime.utcnow()
                }
            })
            raise e


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

    worker = CodeAnalyticsFrameWorker(args.config)
    worker.start()

if __name__ == "__main__":
    __main__()
