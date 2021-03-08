import argparse
import logging
import os
import sys
from . import commands

log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--token',
        default=os.environ.get('DAP_TOKEN'),
        help='API token from your account homepage (defaults to $DAP_TOKEN in the environment)'
    )
    parser.add_argument(
        '--service',
        default=os.environ.get('DAP_SERVICE', 'https://dap.xwcl.science'),
        help='service endpoint (defaults to $DAP_SERVICE if present, or https://dap.xwcl.science)'
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.set_defaults(command_cls=None)
    subps = parser.add_subparsers(title='subcommands',
                                  description='valid subcommands')

    for key, command_cls in commands.REGISTRY.items():
        subp = subps.add_parser(key)
        subp.set_defaults(command_cls=command_cls)
        command_cls.add_arguments(subp)
    
    args = parser.parse_args()
    if args.command_cls is None:
        parser.print_help()
        sys.exit(1)    

    logging.basicConfig(level='INFO' if not args.verbose else 'DEBUG')
    self.log.debug(f'Verbose logging: {args.verbose}')
    
    command = args.command_cls(args)
    sys.exit(command.main())
