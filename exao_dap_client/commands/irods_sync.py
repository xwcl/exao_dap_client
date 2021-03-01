import argparse
import orjson
import os
import os.path
import pathlib
import sys
import warnings
import logging

from .. import utils, data_store

log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('source_dir', help='Local filesystem directory to sync from')
    parser.add_argument('destination_dir', help='iRODS collection to sync to')
    args = parser.parse_args()
    logging.basicConfig(level='INFO' if not args.verbose else 'DEBUG')
    logging.getLogger('irods').setLevel('WARN')
    log.debug(f'Verbose logging: {args.verbose}')
    src = args.source_dir
    if not os.path.isdir(src):
        raise FileNotFoundError(f"Directory not found: {src}")
    dest = args.destination_dir
    data_store.sync_to_irods(src, dest)
    sys.exit(0)
