import hashlib
import re
import os.path
from astropy.io import fits
import dateutil.parser, dateutil.tz
from dateutil.utils import default_tzinfo

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

        {'metadata':
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
    
    if re.match(r'.+\.fits?$', payload['filename']) is None:
        return payload
    hdulist = fits.open(file_handle)
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
    return {'metadata': {'fits': data}}

DATE_KEYWORDS = ('DATE-OBS', 'DATE')

def _parse_datetime(value):
    dt = default_tzinfo(dateutil.parser.parse(value), dateutil.tz.UTC)
    return dt.astimezone(tz=dateutil.tz.UTC)

def date_extractor(payload, file_handle):
    '''Post-process extracted metadata to find creation timestamp
    if present and add it under key 'created_at' after adjusting to
    UTC. (Times without timezone / offset info are presumed UTC.)

    Finds the first occurrence of a header named any of `DATE_KEYWORDS`
    in the primary headers or, failing that, any extension, returning
    the first that parses successfully.

    Supplies `created_at` key for payload.
    '''
    if 'fits' in payload['metadata']:
        headers = payload['metadata']['fits']
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

def _read_in_chunks(file_object, chunk_size=2**30):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def checksum_extractor(payload, file_handle):
    file_handle.seek(0)
    md5sum = hashlib.md5()
    for chunk in _read_in_chunks(file_handle):
        md5sum.update(chunk)
    return {'checksum': md5sum.hexdigest()}

EXTRACTOR_STACK = (
    fits_extractor,
    date_extractor,
    checksum_extractor,
)

def make_payload(filename, file_like=None):
    if file_like is None:
        fh = open(filename, 'rb')
    else:
        fh = file_like
    try:
        payload = {'filename': filename}
        for extractor_func in EXTRACTOR_STACK:
            payload_update = extractor_func(payload, fh)
            payload = merge_payload(payload, payload_update)
    finally:
        if file_like is None:
            fh.close()
    return payload