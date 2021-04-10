import argparse
import logging
import os
import sys
from . import config
from .commands import sync, ingest, extract_info

log = logging.getLogger(__name__)

COMMANDS = {sync.Sync, ingest.Ingest, extract_info.ExtractInfo}


def main():
    parser = argparse.ArgumentParser()
    config.add_cli_options(parser)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.set_defaults(command_cls=None)
    subps = parser.add_subparsers(title='subcommands',
                                  description='valid subcommands')

    for command_cls in COMMANDS:
        cmd = command_cls.name
        print(f'{cmd=}')
        assert cmd is not None
        subp = subps.add_parser(cmd, help=command_cls.help)
        print(f'{subp=}')
        subp.set_defaults(command_cls=command_cls)
        command_cls.add_arguments(subp)
    
    args = parser.parse_args()
    if args.command_cls is None:
        parser.print_help()
        sys.exit(1)    

    logging.basicConfig(level='INFO' if not args.verbose else 'DEBUG')
    log.debug(f'Verbose logging: {args.verbose}')
    
    command = args.command_cls(args)
    sys.exit(command.run())
