import argparse
import logging
from fsspec.registry import filesystem
import orjson
import os.path
import sys
import warnings

from .base import Command
from .. import datum, data_store

log = logging.getLogger(__name__)

class ExtractInfo(Command):
    name = "extract_info"
    help = "Extract metadata and output the file's info payload as understood by the platform"

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        super(ExtractInfo, ExtractInfo).add_arguments(parser)
        parser.add_argument('filename', help='Filename in any supported format to generate a payload for')

    def main(self):
        fn = self.args.filename
        fs = data_store.get_fs(fn)
        if not fs.exists(fn) or not fs.info(fn)['type'] == 'file':
            print(f'{repr(fn)} is not a recognized path to a file', file=sys.stderr)
            sys.exit(1)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with fs.open(fn) as fh:
                payload = datum.extract_info(fh)
        print(orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode('utf8'))
        sys.exit(0)
