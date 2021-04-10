import logging
import os
import re
import pathlib
import threading
from urllib.parse import urlparse, urljoin

from irods.session import iRODSSession
import fsspec
import irods_fsspec
irods_fsspec.register()

from . import utils
from .config import get_config

log = logging.getLogger(__name__)
_LOCAL = threading.local()
_LOCAL.filesystems = {}

def irods_get_fs():
    if not hasattr(_LOCAL, 'irodsfs'):
        config = get_config()
        fs = fsspec.filesystem('irods', **irods_fsspec.irods_config_from_url(config.IRODS_URL))
        _LOCAL.irodsfs = fs
    return _LOCAL.irodsfs

IGNORED_FILENAMES_RE = re.compile(r'__pycache__|\.+')

def name_is_ignored(file_or_dir_name):
    if IGNORED_FILENAMES_RE.match(file_or_dir_name):
        return True
    return False

def join(*args):
    res = urlparse(args[0])
    new_path = os.path.join(res.path, *args[1:])
    return args[0].replace(res.path, new_path)

def basename(path):
    res = urlparse(path)
    return os.path.basename(res.path)

def get_fs(path) -> fsspec.spec.AbstractFileSystem:
    '''Obtain a concrete fsspec filesystem from a path using
    the protocol string (if any; defaults to 'file:///') and 
    `_get_kwargs_from_urls` on the associated fsspec class. The same
    instance will be returned if the same kwargs are used multiple times
    in the same thread.

    Note: Won't work when kwargs are required but not encoded in the
    URL.
    '''
    scheme = urlparse(path).scheme
    proto = scheme if scheme != '' else 'file'
    cls = fsspec.get_filesystem_class(proto)
    if hasattr(cls, '_get_kwargs_from_url'):
        kwargs = cls._get_kwargs_from_urls(path)
    else:
        kwargs = {}
    key = (proto,) + tuple(kwargs.items())
    if not hasattr(_LOCAL, 'filesystems'):
        _LOCAL.filesystems = {}   # unclear why this is not init at import in dask workers
    if key not in _LOCAL.filesystems:
        fs = cls(**kwargs)
        _LOCAL.filesystems[key] = fs
    return _LOCAL.filesystems[key]

def copy_between_filesystems(
    src: str, srcfs: fsspec.spec.AbstractFileSystem, 
    dest: str, destfs: fsspec.spec.AbstractFileSystem
):
    log.debug(f'Copying {src} from {srcfs} to {dest} on {destfs}')
    with destfs.open(dest, 'wb') as dest_fh, srcfs.open(src, 'rb') as src_fh:
        for chunk in utils.read_in_chunks(src_fh):
            dest_fh.write(chunk)

def sync_single_file(
    src, dest,
    src_checksum=None, src_size=None, srcfs=None,
    dest_checksum=None, dest_size=None, destfs=None,
    checksum=utils.md5sum,
    force_overwrite=False
):
    '''Sync the file at path `dest` so that it contains the same bytes
    as `src`. The decision of whether to update `dest` depends on both
    the size and the contents of the file. The file size as reported by
    `fsspec.spec.AbstractFileSystem.size` or optionally passed in
    `src_size` and `dest_size` (if already known, to save a network
    call) is compared, and any discrepancy means `dest` is updated.
    If the sizes are identical, checksums are compared from
    either `src_checksum` and `dest_checksum` (passed in by the caller
    for the same reasons) or recomputed with `checksum`
    (`utils.md5sum` by default). When the checksums differ, `dest` will
    be overwritten with `src`.

    If `force_overwrite` is `True`, `dest` will be overwritten with
    `src` regardless.

    Note: `fsspec.AbstractFileSystem.checksum` depends on the particular
    remote filesystem implementation, and may not be comparable between
    two different ones. This is why the caller must choose to pass them
    in.

    Note: If both `src` and `dest` are remote, the same size, and no
    checksum is provided, they will both be downloaded and checksummed
    locally to decide whether to sync. This may ultimately use more
    bandwidth and be slower than blindly overwriting.
    
    Parameters
    ----------
    src : str
    dest : str
    src_checksum : str or None
    src_size : int or None
        size in bytes, None to obtain from filesystem
    srcfs : fsspec.spec.AbstractFileSystem subclass
        existing filesystem instance
    dest_checksum : str or None
    dest_size : int or None
        size in bytes, None to obtain from filesystem
    destfs : fsspec.spec.AbstractFileSystem subclass
        existing filesystem instance
    checksum : callable
        callable passed an open file-like object to checksum
        and returning a string
    force_overwrite : bool
        short-circuit the comparisons and just overwrite
    '''
    srcfs = get_fs(src) if srcfs is None else srcfs
    destfs = get_fs(dest) if destfs is None else destfs
    if src_size is None:
        src_size = srcfs.size(src)
    if dest_size is None and destfs.exists(dest):
        dest_size = destfs.size(dest)
    overwrite = True
    if not force_overwrite and src_size == dest_size:
        if src_checksum is None:
            src_fh = srcfs.open(src)
            src_checksum = checksum(src_fh)
        if dest_checksum is None:
            dest_fh = destfs.open(dest)
            dest_checksum = checksum(dest_fh)
        if src_checksum == dest_checksum:
            overwrite = False
    overwrite = overwrite or force_overwrite
    if overwrite:
        if srcfs is destfs:
            log.debug(f'Copying {src} to {dest} with {srcfs}')
            srcfs.copy(src, dest)
        else:
            copy_between_filesystems(
                src, srcfs,
                dest, destfs
            )
    else:
        log.debug(f'Skipping {src=} {src_size=} {src_checksum=} / {dest=} {dest_size=} {dest_checksum=}')
    return overwrite

def _filenames_lookup(fs, path):
    contents = fs.ls(path, detail=True)
    files = {}
    for entry in contents:
        if name_is_ignored(entry['name']):
            continue
        if entry['type'] == 'file':
            key = os.path.basename(entry['name'])
            files[key] = entry
    return files

def sync(src, dest, checksum=utils.md5sum, force_overwrite=False):
    '''Sync `src` to `dest`, using any fsspec compatible URL for
    either (including local paths). See `sync_single_file` for
    details on how.

    Parameters
    ----------
    src
        path to a file or directory in a supported filesystem (local,
        iRODS, or any fsspec-supported remote data store)
    dest
        path to a file or directory in a supported filesystem
    checksum : callable (default: utils.md5sum)
        checksum callable accepting file-like object and returning
        its hex digest as str
    force_overwrite : bool (default: False)
        set True if destination files should be overwritten without
        checking their checksums (in other words, if you know it's more
        efficient to just send the files rather than compute their
        checksums)
    '''
    srcfs = get_fs(src)
    src_url = urlparse(src)
    src_path = os.path.abspath(src_url.path) if src_url.scheme in ('file', '') else src_url.path
    destfs = get_fs(dest)
    dest_url = urlparse(dest)
    dest_path = os.path.abspath(dest_url.path) if dest_url.scheme in ('file', '') else dest_url.path

    for dirpath, dirnames, filenames in srcfs.walk(src_path):
        if name_is_ignored(dirpath):
            continue
        # collect list of contents of source dir from local or remote fs
        # and filter out the files to sync
        # TODO this is redundant with `walk` but unless it's too slow
        # it's not worth reimplementing walk
        src_files = _filenames_lookup(srcfs, dirpath)

        the_dir = pathlib.Path(dirpath)
        dest_dir_path = os.path.join(dest_path, the_dir.relative_to(src_path))

        # Collect any existing files and their checksums
        if not destfs.isdir(dest_dir_path):
            log.debug(f'No existing directory at {dest_dir_path}, making one')
            destfs.mkdir(dest_dir_path)
            dest_files = {}
        else:
            log.debug(f"Existing collection {dest_dir_path}")
            dest_files = _filenames_lookup(destfs, dest_dir_path)
            log.debug(f'Collected existing files {list(dest_files.keys())}')
        
        # Loop over local files, computing and comparing checksums
        # if they exist on the remote, then upload if needed
        # TODO this may benefit from parallelization
        for fn, src_entry in src_files.items():
            src_file_path = str(the_dir.joinpath(fn))
            src_size = src_entry['size']
            src_checksum = None

            dest_file_path = os.path.join(dest_dir_path, fn)
            dest_size = None
            dest_checksum = None

            if fn in dest_files:
                dest_entry = dest_files[fn]
                dest_size = dest_entry['size']
                if 'checksum' in src_entry and srcfs is destfs:
                    # trust the filesystem's checksums are comparable
                    # regardless of which it is
                    src_checksum = src_entry['checksum']
                    dest_checksum = dest_entry['checksum']
                elif checksum is utils.md5sum:
                    # we know iRODS checksums are md5, otherwise who knows
                    if isinstance(srcfs, irods_fsspec.IRODSFileSystem):
                        src_checksum = src_entry['checksum']
                    if isinstance(destfs, irods_fsspec.IRODSFileSystem):
                        dest_checksum = dest_entry['checksum']

            sync_single_file(
                src_file_path,
                dest_file_path,
                src_size=src_size,
                src_checksum=src_checksum,
                srcfs=srcfs,
                dest_size=dest_size,
                dest_checksum=dest_checksum,
                destfs=destfs,
                checksum=checksum,
                force_overwrite=force_overwrite
            )
