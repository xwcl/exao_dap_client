import orjson
import requests
from urllib.parse import urljoin
from .config import get_config
from . import __version__

def make_request(method, endpoint, payload):
    config = get_config()
    url = urljoin(config.SERVICE_URL, endpoint)
    headers = {
        'User-Agent': f'exao_dap_client / {__version__}',
        'Content-Type': 'application/json',
        'Authorization': f'Token {config.TOKEN}'
    }
    resp = method(url, headers=headers, data=orjson.dumps(payload))
    resp.raise_for_status()
    return orjson.loads(resp.text)

def get(endpoint, payload):
    return make_request(requests.get, endpoint, payload)

def post(endpoint, payload):
    return make_request(requests.post, endpoint, payload)
