import argparse
import os
import os.path
import logging

from .base import Command
from .. import data_store, datum, dataset

log = logging.getLogger(__name__)

class Ingest(Command):
    name = "ingest"
    help = "Turn a Data Store path into a registered dataset"

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        super(Ingest, Ingest).add_arguments(parser)
        parser.add_argument('data_store_path', help='iRODS collection path to ingest')
        parser.add_argument('identifier', help='Dataset identifier to use (must be unique)')
        parser.add_argument(
            '--source',
            help=f'how these data were obtained ({Command.enum_help(dataset.DatasetSource)})',
            type=Command.make_to_enum(dataset.DatasetSource),
            required=True
        )
        parser.add_argument(
            '--stage',
            help=f'level of processing ({Command.enum_help(dataset.DatasetStage)})',
            type=Command.make_to_enum(dataset.DatasetStage),
            required=True
        )
        parser.add_argument(
            '--kind',
            help=f'purpose of these files ({Command.enum_help(datum.DatumKind)})',
            type=Command.make_to_enum(datum.DatumKind),
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
        data_payloads = datum.init_from_collection(self.args.data_store_path)
        result = dataset.ingest(
            self.args.data_store_path,
            self.args.identifier,
            self.args.source,
            self.args.stage,
            self.args.kind,
            self.args.description,
            self.args.friendly_name,
            data_payloads
        )
        return self.SUCCESS
