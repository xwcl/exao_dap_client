import os.path
from astropy.io import fits



_FITS_IGNORE_KEYWORDS = set(('COMMENT', 'HISTORY', 'SIMPLE', 'EXTEND', 'GCOUNT', 'PCOUNT', 'EXTNAME'))
def extract_fits(file_handle):
    hdulist = fits.open(file_handle)
    data = {}
    # primary extension -> top level keys
    for card in hdulist[0].header.cards:
        if card.keyword in _FITS_IGNORE_KEYWORDS:
            continue
        data[card.keyword] = card.value
    for idx, hdu in enumerate(hdulist[1:], start=1):
        hdr = hdu.header
        extdata = {}
        for card in hdr.cards:
            if card.keyword in _FITS_IGNORE_KEYWORDS:
                continue
            extdata[card.keyword] = card.value
        if 'EXTNAME' in hdr:
            name = f"ext_{hdr['EXTNAME']}"
        else:
            name = f'ext_{idx}'
        data[name] = extdata
    return data

def extract_metadata(filename, file_like=None):
    if file_like is None:
        fh = open(filename, 'rb')
    else:
        fh = file_like
    try:
        extension, extract_func = get_extractor(filename)
        metadata = {extension: extract_func(fh)}
    finally:
        if file_like is None:
            fh.close()
    return metadata

EXTRACTORS = {
    'fits': extract_fits,
    'fit': extract_fits,
}

def get_extractor(filename):
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    try:
        return ext, EXTRACTORS[ext]
    except KeyError:
        raise RuntimeError(f'No extractor configured for file extension "{ext}"')

def register(extension, extract_function):
    global EXTRACTORS
    EXTRACTORS[extension] = extract_function
