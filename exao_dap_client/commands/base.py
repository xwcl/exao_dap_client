import argparse
import os
import sys
import logging

from .. import config

log = logging.getLogger(__name__)

class BaseCommand:
    name = None
    help = None
    SUCCESS = 0
    FAILURE = 1

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.log = logging.getLogger(self.__class__.__name__)
        self.config = config.get_config(args)

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        pass
    @staticmethod
    def make_to_enum(enum):
        def converter(value):
            for enumval in enum:
                if enumval.name.lower() == value.lower():
                    return enumval
            raise argparse.ArgumentTypeError(f"Unrecognized value {value} (must be one of {BaseCommand.enum_help(enum)})")
        return converter
    @staticmethod
    def enum_help(enum):
        help = []
        for enumval in enum:
            help.append(enumval.name.lower())
        return ', '.join(help)
    def main(self):
        raise NotImplementedError("Subclasses must implement a main() method")