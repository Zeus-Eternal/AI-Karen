class Response:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(response=self)

class HTTPError(Exception):
    def __init__(self, response):
        self.response = response


def get(*args, **kwargs):
    return Response()

def post(*args, **kwargs):
    return Response()

def put(*args, **kwargs):
    return Response()

def delete(*args, **kwargs):
    return Response()
