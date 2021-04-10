from enum import Enum
from . import http

class RunState(Enum):
    WAITING = 'waiting'
    STAGE_IN = 'stage_in'
    RUNNING = 'running'
    STAGE_OUT = 'stage_out'
    FAILED = 'failed'
