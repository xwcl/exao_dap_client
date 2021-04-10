import argparse
import orjson
import os
import os.path
import pathlib
import sys
import warnings
import logging

from .base import Command

from .. import utils, data_store

log = logging.getLogger(__name__)

class Sync(Command):
    name = "sync"
    help = "Sync a local filesystem directory to an iRODS collection"

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        super(Sync, Sync).add_arguments(parser)
        parser.add_argument('source_dir', help='path or URL to sync from')
        parser.add_argument('destination_dir', help='path or URL to sync to')
    
    def main(self):
        logging.getLogger('irods').setLevel('WARN')
        src = self.args.source_dir
        dest = self.args.destination_dir
        data_store.sync(src, dest)
        return self.SUCCESS
