#!/usr/bin/env python

from distutils.core import setup
import os
import os.path


def files(basedir, dirs):
    for directory in dirs:
        for (path, _, file_list) in os.walk(os.path.join(basedir, directory)):
            for filename in file_list:
                yield os.path.relpath(os.path.join(path, filename), basedir)


setup(
    name='ceburasko',
    version='4.0',
    description='Ceburasko Django app',
    long_description='Django application for store crashes',
    author='Alexey Tamarevskiy',
    author_email='mirror@inetra.ru',
    packages=['ceburasko', 'ceburasko.context_processors', 'ceburasko.migrations', 'ceburasko.templatetags', ],
    package_data={
        'ceburasko': list(files('ceburasko', ('static', 'templates', 'data', ))),
    },
    scripts=[
        'ceburasko-binary-id',
        'ceburasko-upload-binaries',
        'ceburasko-valgrind',
        'ceburasko-find-binary-id',
    ],
    license="GPLv2",
)


