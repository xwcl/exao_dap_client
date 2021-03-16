import argparse
import logging
import orjson
import os.path
import sys
import warnings

from ..datum import extract_info

from .base import BaseCommand
from .. import data_store, datum, dataset

log = logging.getLogger(__name__)

class ExtractInfo(BaseCommand):
    help = "Extract metadata and output the file's info payload as understood by the platform"

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument('filename', help='Filename in any supported format to generate a payload for')
    def main(self):
        fn = self.args.filename
        if not os.path.exists(fn) or not os.path.isfile(fn):
            print(f'File not found: {fn}', file=sys.stderr)
            sys.exit(1)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            payload = extract_info(fn)
        print(orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode('utf8'))
        sys.exit(0)
