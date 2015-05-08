from subprocess import Popen, PIPE
import hashlib
import os


class ReadElfFailed(Exception):
    pass


class NoBuildId(Exception):
    pass


def binary_id_from_coredump(coredump):
    eu_unstrip = Popen(["eu-unstrip", "-n", "--core", coredump], stdout=PIPE, stderr=PIPE)
    if eu_unstrip.wait() != 0:
        raise ReadElfFail(unstrip.stderr.read().strip())
    for line in eu_unstrip.stdout.readlines():
        module_info = line.lower().split()
        build_id = module_info[1]
        module_name = module_info[4]
        if module_name == '[exe]':
            if build_id == '-':
                raise NoBuildId("No build-id embedded")
            return "%s:%s" % ("build-id", build_id.split('@')[0])
    raise NoBuildId("No build-id found")


def binary_id_from_elf_headers(filename):
    return binary_id_from_coredump(filename)


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
        except:
            return binary_id_from_content(filename)
