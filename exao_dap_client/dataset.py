from enum import Enum

class DatasetSource(Enum):
    ON_SKY = 'on_sky'
    LAB = 'lab'
    SIMULATION = 'simulation'

class DatasetStage(Enum):
    RAW = 'raw'
    CALIBRATED = 'calibrated'
    REDUCED = 'reduced'

class DatasetState(Enum):
    PENDING = 'pending'
    COMPLETE = 'complete'
