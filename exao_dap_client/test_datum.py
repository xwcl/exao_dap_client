import io
import datetime
from astropy.io import fits
import numpy as np
import dateutil.tz
import dateutil.parser
import pytest
from .datum import make_payload


@pytest.fixture
def example_fits_hdul():
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
    return hdul


def _hdul_to_bytesio(hdul):
    outfile = io.BytesIO()
    hdul.writeto(outfile)
    outfile.seek(0)
    return outfile


@pytest.mark.parametrize("extension", [0, "FOO", 2])
@pytest.mark.parametrize("date_kw", ["DATE", "DATE-OBS"])
def test_extract_date(example_fits_hdul, date_kw, extension):
    hdul = example_fits_hdul
    hdul[extension].header[date_kw] = '2015-11-29T06:10:42.0'
    file_like = _hdul_to_bytesio(hdul)
    payload = make_payload('example.fits', file_like)
    assert payload['created_at'] == datetime.datetime(
        2015, 11, 29, 6, 10, 42,
        tzinfo=dateutil.tz.UTC
    )


def test_extract_fits(example_fits_hdul):
    file_like = _hdul_to_bytesio(example_fits_hdul)
    ref_payload = {
        'filename': 'example.fits',
        'checksum': 'f1550321a1d6e909d767e13d0d789453',
        'metadata': {
            'fits': {
                'KEYWORD': 'value',
                'INTKW': 1,
                'FLOATKW': 1.5,
                'BOOLKW': True,
                'BITPIX': -64,
                'NAXIS': 2,
                'NAXIS1': 64,
                'NAXIS2': 64,
                'ext': {
                    'FOO': {
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
                    'idx_2': {
                        'KEYWORD': 'value',
                        'INTKW': 1,
                        'FLOATKW': 1.5,
                        'BOOLKW': True,
                        'BITPIX': -64,
                        'NAXIS': 2,
                        'NAXIS1': 64,
                        'NAXIS2': 64,
                        'XTENSION': 'IMAGE'
                    }
                }
            }}
    }

    assert make_payload('example.fits', file_like) == ref_payload
