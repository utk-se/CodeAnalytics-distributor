
from requests.auth import HTTPBasicAuth
from .. import log

class CodeAnalyticsDistributorError(RuntimeError):
    pass

class CodeAnalyticsWorker():
    def ping_master():
        r = requests.get(
            this.config["api"]["baseuri"] + "/status"
        )
        log.debug(r)
        log.debug(r.content)
        assert r.ok

    def get_worker_state():
        r = requests.get(
            this.config["api"]["baseuri"] + "/status/worker/" + this.config["api"]["workername"],
        )
        if r.ok:
            return loads(r.text)
        elif r.status_code == requests.codes.unauthorized:
            raise ConnectionRefusedError("unauthorized")
        elif r.status_code == requests.codes.not_found:
            raise RuntimeError(f"Worker status for \'{this.config['api']['workername']}\' not found on server!")
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
            this.config["api"]["baseuri"] + "/status/worker/" + this.config["api"]["workername"],
            data=dumps(data),
            auth=this.config["auth"],
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
