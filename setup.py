#!/usr/bin/env python

from distutils.core import setup
from itertools import chain
import os
import os.path

def files(basedir, dirs):
    for dir in dirs:
        for (path, _, files) in os.walk(os.path.join(basedir, dir)):
            for file in files:
                yield os.path.relpath(os.path.join(path, file), basedir)

setup(
    name = 'ceburasko',
    version = '1.9.2',
    description = 'Ceburasko Django app',
    long_description = 'Django application for store crashes',
    author = 'Alexey Tamarevskiy',
    author_email = 'mirror@inetra.ru',
    packages = [ 'ceburasko' ],
    package_data = { 'ceburasko': list(files('ceburasko', ('static', 'templates'))) } ,
    scripts = [
        'gdb-output-ceburasko-upload',
        'ceburasko-valgrind',
        'valgrind-xml-ceburasko-upload',
    ],
    license = "GPLv2",
)


