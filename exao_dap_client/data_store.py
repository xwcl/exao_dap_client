import logging
import os
import pathlib

import fsspec
import irods_fsspec
irods_fsspec.register()

from . import utils

log = logging.getLogger(__name__)

def sync_to_irods(src_dir, dest_collection):
    '''Sync a directory on the host to a collection path in the
    iRODS data store

    Parameters
    ----------
    src_dir : path
    dest_collection : str (iRODS path)
    '''
    irodsfs = fsspec.filesystem('irods')
    for dirpath, dirnames, filenames in os.walk(src_dir):
        the_dir = pathlib.Path(dirpath)
        # TODO more robust ignore logic
        if the_dir.name[0] == '.' or the_dir.name == '__pycache__':
            continue
        dest_collection_path = os.path.join(dest_collection, the_dir.relative_to(src_dir))

        # Collect any existing files and their checksums
        if not irodsfs.isdir(dest_collection_path):
            log.debug(f'No existing collection at {dest_collection_path}, making one')
            irodsfs.mkdir(dest_collection_path)
            existing_files = {}
        else:
            log.debug(f"Existing collection {dest_collection_path}")
            contents = irodsfs.ls(dest_collection_path)
            existing_files = {}
            for entry in contents:
                if entry['type'] == 'file':
                    key = os.path.basename(entry['name'])
                    existing_files[key] = entry
            log.debug(f'Collected existing data objects {list(existing_files.keys())}')
        
        # Loop over local files, computing and comparing checksums
        # if they exist on the remote, then upload if needed
        # TODO this may benefit from parallelization
        for fn in filenames:
            # TODO more robust ignore logic
            if fn[0] == '.':
                continue
            src_file_path = the_dir.joinpath(fn)
            dest_file_path = os.path.join(dest_collection_path, fn)
            with src_file_path.open('rb') as f:
                if fn in existing_files:
                    local_md5sum = utils.md5sum(f)
                    remote_md5sum = existing_files[fn]['checksum']
                    log.debug(f'{local_md5sum=}, {remote_md5sum=}')
                    if local_md5sum == remote_md5sum:
                        log.debug(f'Skipping upload of {fn} because checksums match')
                        continue
                log.debug(f'Uploading {src_file_path} to {dest_collection_path}')
                irodsfs.put_file(src_file_path, dest_file_path)
