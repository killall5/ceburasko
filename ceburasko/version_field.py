from django.db.models import *
from django.utils.six import with_metaclass


class Version():
    def __init__(self, value=None):
        if isinstance(value, tuple) or isinstance(value, list):
            self.raw = tuple(value[:4])
        else:
            try:
                self.raw = tuple(map(int, value.split('.')))
            except:
                self.raw = tuple()

    def __str__(self):
        return '.'.join(map(str, self.raw))

    def __unicode__(self):
        return self.__str__()

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise NotImplementedError()
        return self.raw < other.raw

    def __le__(self, other):
        if not isinstance(other, Version):
            raise NotImplementedError()
        return self.raw <= other.raw

    def __eq__(self, other):
        if isinstance(other, Version):
            return self.raw == other.raw
        elif isinstance(other, tuple):
            return self.raw == other
        elif isinstance(other, list):
            return self.raw == tuple(other)
        elif other is None:
            return False
        else:
            raise NotImplementedError()


    @property
    def major(self):
        try:
            return self.raw[0]
        except IndexError as e:
            return 0

    @property
    def minor(self):
        try:
            return self.raw[1]
        except IndexError as e:
            return 0

    @property
    def bugfix(self):
        try:
            return self.raw[2]
        except IndexError as e:
            return 0

    @property
    def build(self):
        try:
            return self.raw[3]
        except IndexError as e:
            return 0


class VersionField(with_metaclass(SubfieldBase, IntegerField)):
    def db_type(self, connection):
        return 'bigint'  # Note this won't work with Oracle.

    def to_python(self, value):
        if isinstance(value, Version):
            return value
        if value is None:
            return None
        value, build  = value/1000000, value % 1000000
        value, bugfix = value/10000,   value % 10000
        major, minor  = value/10000,   value % 10000
        return Version((major, minor, bugfix, build))

    def get_prep_value(self, value):
        if value is None:
            return None
        return value.build + 1000000*(value.bugfix + 10000*(value.minor + 10000*value.major))

