import argparse
import os
import os.path
import logging

from .base import BaseCommand
from .. import data_store, datum, dataset

log = logging.getLogger(__name__)

class Ingest(BaseCommand):
    help = "Turn a Data Store path into a registered dataset"

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument('data_store_path', help='iRODS collection path to ingest')
        parser.add_argument('destination_dir', help='iRODS collection to sync to')
        parser.add_argument(
            '--source',
            help=f'how these data were obtained ({BaseCommand.enum_help(dataset.DatasetSource)})',
            type=BaseCommand.make_to_enum(dataset.DatasetSource),
            required=True
        )
        parser.add_argument(
            '--stage',
            help=f'level of processing ({BaseCommand.enum_help(dataset.DatasetStage)})',
            type=BaseCommand.make_to_enum(dataset.DatasetSource),
            required=True
        )
        parser.add_argument(
            '--kind',
            help=f'purpose of these files ({BaseCommand.enum_help(datum.DatumKind)})',
            type=BaseCommand.make_to_enum(dataset.DatasetSource),
            required=True
        )
        parser.add_argument(
            '--description',
            help=f'Descriptive text',
        )
        parser.add_argument(
            '--friendly-name',
            help=f'Friendly name for this dataset',
        )

    def main(self):
        print(self.args)
        return self.SUCCESS
