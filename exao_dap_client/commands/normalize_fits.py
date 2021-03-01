import argparse
import logging
import os
from astropy.io import fits
import warnings

log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Filename in any supported format to generate a payload for', nargs='+')
    parser.add_argument('-o', '--outfolder', help='Destination folder for updated files', nargs='?', default='./normalized_fits')
    parser.add_argument('-f', '--force-overwrite', help='Whether to overwrite existing files', action='store_true')
    # TODO options to set keywords on all files
    args = parser.parse_args()
    fn_list = args.filename
    outfolder = args.outfolder
    overwrite = args.force_overwrite
    os.makedirs(outfolder, exist_ok=True)
    for fn in fn_list:
        with open(fn, 'rb') as f:
            basename = os.path.basename(fn)
            hdul = fits.open(f)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                hdul.verify('fix')  # TODO this can't handle the corrupted Clio split header
                outpath = os.path.join(outfolder, basename)
                hdul.writeto(outpath, overwrite=overwrite)
                log.info(f'Validated {fn} and wrote to {outpath}')
