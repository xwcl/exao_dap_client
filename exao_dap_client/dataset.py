from enum import Enum
from . import http


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

def ingest(data_store_path, identifier, source, stage, kind, description, friendly_name, data_payloads):
    payload = {
        'identifier': identifier,
        'source_path': data_store_path,
        'source': source.value,
        'stage': stage.value,
        'kind': kind.value,
        'data': data_payloads,
    }
    # optional
    if friendly_name:
        payload['friendly_name'] = friendly_name
    if description:
        payload['description'] = description
    return http.post('/api/v1/registrar/datasets/', payload)
