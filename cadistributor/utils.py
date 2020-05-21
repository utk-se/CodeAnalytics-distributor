
import urllib

class CodeAnalyticsError(Exception):
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

def ensureVersionStringMongoSafe(str):
    if '.' in str:
        raise CodeAnalyticsError("Version ID/key string may not use the dot, please replace it!", 400)
    if '$' in str:
        raise CodeAnalyticsError("Version ID/key string may not use the dollar sign, please replace it!", 400)

def escape_url(url):
    return urllib.parse.quote_plus(url)
