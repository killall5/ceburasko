from subprocess import Popen, PIPE
import hashlib
import os

def exe_id_from_hash(filename, hash_name = "sha256"):
    hash = hashlib.new(hash_name)
    with open(filename) as f:
        hash.update(f.read())
    return "%s:%s" % (hash_name, hash.hexdigest())

def exe_id_from_build_id(filename):
    readelf = Popen(["readelf", "-n", filename], stdout=PIPE, stderr=PIPE)
    if readelf.wait() != 0:
        raise Exception(readelf.stderr.read().strip())
    for line in readelf.stdout.readlines():
        line = line.lower().strip()
        if 'build id:' in line:
            return "%s:%s" % ("build-id", line.split()[-1])
    raise Exception("No build-id in elf notes")

def exe_id(filename):
    if os.name == "nt":
        return exe_id_from_hash(filename)
    else:
        try:
            return exe_id_from_build_id(filename)
        except:
            return exe_id_from_hash(filename) 


