from subprocess import Popen, PIPE
import hashlib
import os


class ReadElfFailed(Exception):
    pass


class NoBuildId(Exception):
    pass


def binary_id_from_elf_headers(filename):
    readelf = Popen(["eu-readelf", "-n", filename], stdout=PIPE, stderr=PIPE)
    if readelf.wait() != 0:
        raise ReadElfFailed(readelf.stderr.read().strip())
    for line in readelf.stdout.readlines():
        line = line.lower().strip()
        if 'build id:' in line:
            return "%s:%s" % ("build-id", line.split()[-1])
    raise NoBuildId("No build-id in elf notes")


def binary_id_from_content(filename, hash_name="sha256"):
    hash_fn = hashlib.new(hash_name)
    with open(filename) as f:
        hash_fn.update(f.read())
    return "%s:%s" % (hash_name, hash_fn.hexdigest())


def binary_id(filename):
    if os.name == "nt":
        return binary_id_from_content(filename)
    else:
        try:
            return binary_id_from_elf_headers(filename)
        except ReadElfFailed as e:
            return binary_id_from_content(filename)
        except NoBuildId as e:
            return binary_id_from_content(filename)
