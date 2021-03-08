from .ingest import Ingest
from .sync import Sync

REGISTRY = {}

def register(command_cls):
    name = command_cls.name if command_cls.name is not None else command_cls.__name__.lower()
    REGISTRY[name] = command_cls

register(Sync)
register(Ingest)
