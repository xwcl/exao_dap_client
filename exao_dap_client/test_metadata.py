import io
import numpy as np
from astropy.io import fits
import pytest

from .metadata import extract_fits


def test_extract_fits():
    def _populate(hdr):
        hdr['KeyWord'] = 'value'
        hdr['INTKW'] = 1
        hdr['FLOATKW'] = 1.5
        hdr['BOOLKW'] = True
    hdul = fits.HDUList()
    phdu = fits.PrimaryHDU(np.zeros((64, 64)))
    _populate(phdu.header)
    hdul.append(phdu)
    ihdu = fits.ImageHDU(np.ones((64, 64)), name='FOO')
    _populate(ihdu.header)
    hdul.append(ihdu)
    shdu = fits.ImageHDU(2 * np.ones((64, 64)))
    _populate(shdu.header)
    hdul.append(shdu)
    outfile = io.BytesIO()
    hdul.writeto(outfile)
    outfile.seek(0)

    metadata = {
        'KEYWORD': 'value',
        'INTKW': 1,
        'FLOATKW': 1.5,
        'BOOLKW': True,
        'BITPIX': -64,
        'NAXIS': 2,
        'NAXIS1': 64,
        'NAXIS2': 64,
        'ext_FOO': {
            'KEYWORD': 'value',
            'INTKW': 1,
            'FLOATKW': 1.5,
            'BOOLKW': True,
            'BITPIX': -64,
            'NAXIS': 2,
            'NAXIS1': 64,
            'NAXIS2': 64,
            'XTENSION': 'IMAGE'
        },
        'ext_2': {
            'KEYWORD': 'value',
            'INTKW': 1,
            'FLOATKW': 1.5,
            'BOOLKW': True,
            'BITPIX': -64,
            'NAXIS': 2,
            'NAXIS1': 64,
            'NAXIS2': 64,
            'XTENSION': 'IMAGE'
        },
    }
    assert extract_fits(outfile) == metadata
