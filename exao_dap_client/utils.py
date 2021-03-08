import hashlib

def read_in_chunks(file_object, chunk_size=2**30):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def size_and_md5sum(str_or_file_handle):
    md5_hasher = hashlib.md5()
    total_size = 0
    if not isinstance(str_or_file_handle, str):
        str_or_file_handle.seek(0)
        for chunk in read_in_chunks(str_or_file_handle):
            bytes_read = len(chunk)
            md5_hasher.update(chunk)
            total_size += bytes_read
    else:
        total_size = len(str_or_file_handle)
        md5_hasher.update(str_or_file_handle.encode('utf8'))
    return total_size, md5_hasher.hexdigest()

def md5sum(str_or_file_handle):
    _, checksum = size_and_md5sum(str_or_file_handle)
    return checksum
