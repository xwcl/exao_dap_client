import os
from dataclasses import dataclass
from functools import lru_cache
import threading
from typing import Union

DEFAULT_SERVICE_URL = "https://dap.xwcl.science"
DEFAULT_IRODS_URL = "irods://data.cyverse.org"

_LOCAL = threading.local()

@dataclass
class Config:
    SERVICE_URL: str
    TOKEN: str
    IRODS_URL: str

def get_config(args=None) -> Config:
    if not hasattr(_LOCAL, 'config'):
        kwargs = {
            'SERVICE_URL': os.environ.get('DAP_SERVICE_URL', DEFAULT_SERVICE_URL),
            'TOKEN': os.environ.get('DAP_TOKEN'),
            'IRODS_URL': os.environ.get('DAP_IRODS_URL', DEFAULT_IRODS_URL),
        }
        if args:
            if args.service_url:
                kwargs['SERVICE_URL'] = args.service_url
            if args.token:
                kwargs['TOKEN'] = args.token
            if args.irods_url:
                kwargs['IRODS_URL'] = args.irods_url
        _LOCAL.config = Config(**kwargs)
    return _LOCAL.config

def add_cli_options(parser):
    parser.add_argument(
        '--token',
        help='API token from your account homepage (defaults to $DAP_TOKEN in the environment, required)'
    )
    parser.add_argument(
        '--service-url',
        help=f'service endpoint (defaults to $DAP_SERVICE if present, or {DEFAULT_SERVICE_URL})'
    )
    parser.add_argument(
        '--irods-url',
        help=f'override iRODS connection information (default uses ~/.irods info, falling back to $DAP_IRODS_URL if present, or {DEFAULT_IRODS_URL})'
    )
