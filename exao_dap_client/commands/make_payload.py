import argparse
import json
import os.path
import sys
import warnings

from ..datum import make_payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Filename in any supported format to generate a payload for')
    args = parser.parse_args()
    fn = args.filename
    if not os.path.exists(fn) or not os.path.isfile(fn):
        print(f'File not found: {fn}', file=sys.stderr)
        sys.exit(1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        payload = make_payload(args.filename)
    print(json.dumps(payload, indent=2))
    sys.exit(0)
