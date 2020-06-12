
import datetime
import requests
from bson.json_util import loads, dumps
from requests.auth import HTTPBasicAuth
from .. import log

class CodeAnalyticsDistributorError(RuntimeError):
    pass

class CodeAnalyticsWorker():
    def ping_master(self):
        r = requests.get(
            self.config["api"]["baseuri"] + "/status",
            auth=self.config["auth"],
        )
        log.debug(r)
        log.debug(r.content)
        assert r.ok

    def get_worker_state(self):
        r = requests.get(
            self.config["api"]["baseuri"] + "/status/worker/" + self.config["api"]["workername"],
        )
        if r.ok:
            return loads(r.text)
        elif r.status_code == requests.codes.unauthorized:
            raise ConnectionRefusedError("unauthorized")
        elif r.status_code == requests.codes.not_found:
            raise RuntimeError(f"Worker status for \'{self.config['api']['workername']}\' not found on server!")
        else:
            log.error(f"Unknown response: {r.status_code}")
            raise RuntimeError(f"Unknown response: {r.status_code}")

    def checkin(self, status: str = "nothing", state: dict = {}):
        now = datetime.datetime.utcnow()
        data = self.get_worker_state() or {}
        newdata={
            "status": status,
            "lastcheckin": now,
            "lastcheckin_human": now.strftime('%F %T %z')
        }
        newdata.update(state)
        data.update(newdata)
        # log.debug(f"Putting data: {dumps(data)}")
        r = requests.put(
            self.config["api"]["baseuri"] + "/status/worker/" + self.config["api"]["workername"],
            data=dumps(data),
            auth=self.config["auth"],
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
