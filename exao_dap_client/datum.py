from enum import Enum
import hashlib
import re
import os.path
from astropy.io import fits
import dateutil.parser, dateutil.tz
from dateutil.utils import default_tzinfo

from . import utils, data_store

class DatumKind(Enum):
    SCIENCE = 'science'
    CALIBRATION = 'calibration'
    REFERENCE = 'reference'
    PRODUCT = 'product'

_FITS_IGNORE_KEYWORDS = set(('COMMENT', 'HISTORY', 'SIMPLE', 'EXTEND', 'GCOUNT', 'PCOUNT', 'EXTNAME'))

def merge_payload(original_payload, new_payload):
    final_payload = original_payload.copy()
    for key in new_payload:
        if key not in original_payload:
            final_payload[key] = new_payload[key]
        else:
            if isinstance(original_payload[key], list):
                final_payload[key].extend(new_payload[key])
            elif isinstance(original_payload[key], dict):
                final_payload[key] = merge_payload(original_payload[key], final_payload[key])
            else:
                final_payload[key] = new_payload[key]
    return final_payload

def fits_extractor(payload, file_handle):
    '''If the payload['filename'] value has a FITS extension,
    parse `file_handle` as FITS and construct dictionaries
    from the headers to produce a payload for merging into the final
    value::

        {'meta':
            {'fits': {
                'KEYWORD': value,
                'KEYWORD': value,
                ...
                'ext': {
                    'MYEXT': {'KEYWORD': value, ...},
                    'ext_2': {'KEYWORD': value, ...}
                }
            }}
        }    
    '''
    try:
        hdulist = fits.open(file_handle)
    except Exception:
        return payload
    # primary extension -> top level keys
    data = {}
    for card in hdulist[0].header.cards:
        if card.keyword in _FITS_IGNORE_KEYWORDS:
            continue
        data[card.keyword] = card.value
    extensions = {}
    for idx, hdu in enumerate(hdulist[1:], start=1):
        hdr = hdu.header
        extdata = {}
        for card in hdr.cards:
            if card.keyword in _FITS_IGNORE_KEYWORDS:
                continue
            extdata[card.keyword] = card.value
        if 'EXTNAME' in hdr:
            name = hdr['EXTNAME']
        else:
            name = f'idx_{idx}'
        extensions[name] = extdata
    data['ext'] = extensions
    return {'meta': {'fits': data}}

DATE_KEYWORDS = ('DATE-OBS', 'DATE')

def _parse_datetime(value):
    dt = default_tzinfo(dateutil.parser.parse(value), dateutil.tz.UTC)
    return dt.astimezone(tz=dateutil.tz.UTC)

def date_extractor(payload, file_handle):
    '''Post-process extracted meta to find creation timestamp
    if present and add it under key 'created_at' after adjusting to
    UTC. (Times without timezone / offset info are presumed UTC.)

    Finds the first occurrence of a header named any of `DATE_KEYWORDS`
    in the primary headers or, failing that, any extension, returning
    the first that parses successfully.

    Supplies `created_at` key for payload.
    '''
    if 'fits' in payload['meta']:
        headers = payload['meta']['fits']
        for kw in DATE_KEYWORDS:
            if kw in headers:
                try:
                    return {'created_at': _parse_datetime(headers[kw])}
                except ValueError:
                    pass
            for extkey in headers['ext']:
                if kw in headers['ext'][extkey]:
                    try:
                        return {'created_at': _parse_datetime(headers['ext'][extkey][kw])}
                    except ValueError:
                        pass
    return {}


def checksum_size_extractor(payload, file_handle):
    size_bytes, md5sum = utils.size_and_md5sum(file_handle)
    return {'checksum_md5': md5sum, 'size_bytes': size_bytes}

EXTRACTOR_STACK = (
    fits_extractor,
    date_extractor,
    checksum_size_extractor,
)

def extract_info(filename_or_file):
    if isinstance(filename_or_file, str):
        fh = open(filename_or_file, 'rb')
    else:
        fh = filename_or_file
    try:
        payload = {}
        for extractor_func in EXTRACTOR_STACK:
            payload_update = extractor_func(payload, fh)
            payload = merge_payload(payload, payload_update)
    finally:
        if not isinstance(filename_or_file, str):
            fh.close()
    return payload

def extract_all_info(filenames_or_files, minimal=False, file_likes=None):
    payloads = []
    for fn_or_fh in filenames_or_files:
        if isinstance(fn_or_fh, str):
            fh = open(fn_or_fh, 'rb')
        else:
            fh = fn_or_fh
        payloads.append(extract_info(fh))
    return payloads

def init_from_collection(src_collection, default_kind=DatumKind.SCIENCE):
    irodsfs = data_store.irods_get_fs()
    results = []
    for entry in irodsfs.ls(src_collection):
        payload = {
            'kind': default_kind,
            'filename': os.path.basename(entry['name'])
        }
        results.append(payload)
    return results
