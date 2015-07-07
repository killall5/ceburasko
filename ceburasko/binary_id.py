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
    eu_readelf = Popen(["eu-readelf", "-n", filename], stdout=PIPE, stderr=PIPE)
    if eu_readelf.wait() != 0:
        raise ReadElfFailed(eu_readelf.stderr.read().strip())
    for line in eu_readelf.stdout.readlines():
        if 'Build ID' in line:
            build_id = line.split()[-1]
            return "%s:%s" % ("build-id", build_id)
    raise NoBuildId("No build-id found")


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


def is_exe(path):
    if path.lower().endswith('.exe'):
        return True
    return os.path.isfile(path) and os.access(path, os.X_OK)


import sqlite3


def find_by_binary_id(needle_id, paths=[], cache='binary_id_cache.db'):
    if cache:
        conn = sqlite3.connect(cache)
        cur = conn.cursor()
        try:
            cur.execute('create table binary_id_cache(binary_id, abs_path)')
        except:
            pass
        cur.execute('select abs_path from binary_id_cache where binary_id = ?', (needle_id, ))
        res = cur.fetchone()
        if res:
            res = res[0]
            try:
                real_id = binary_id(res)
                if real_id == needle_id:
                    cur.close()
                    conn.close()
                    return res
            except:
                pass
            cur.execute('delete from binary_id_cache where binary_id = ?', (needle_id, ))
    if not paths:
        paths = os.getenv("PATH", ".").split(":")
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                abs_path = os.path.join(dirpath, filename)
                if is_exe(abs_path):
                    if binary_id(abs_path) == needle_id:
                        if cache:
                            try:
                                cur.execute('insert into binary_id_cache values(?, ?)', (needle_id, abs_path))
                            except Exception as e:
                                print e
                                cur.execute('update binary_id_cache set abs_path = ? where binary_id = ?', (abs_path, needle_id))
                            cur.close()
                            conn.commit()
                            conn.close()
                        return abs_path
