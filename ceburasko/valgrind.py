import xml.etree.ElementTree as ET
import os


class Frame():
    def __init__(self):
        self.function = None
        self.dir = None
        self.file = None
        self.line = None

    def __str__(self):
        res = {
            'function': '??',
            'src_line': ''
        }
        if not self.function is None:
            res['function'] = self.function
        if not (self.file is None and self.line is None):
            res['src_line'] = ' at %s:%s' % (self.file, self.line)
        return '%(function)s%(src_line)s' % res

    @property
    def full_filename(self):
        if self.dir is None:
            return self.file
        else:
            return os.path.join(self.dir, self.file)


def parse_fn(fn, frame):
    frame.function = fn.text


def parse_dir(dir, frame):
    frame.dir = dir.text


def parse_file(file, frame):
    frame.file = file.text


def parse_line(line, frame):
    frame.line = line.text


def parse_kind(kind, accident):
    accident['kind'] = kind.text


def parse_what(what, accident):
    accident['what'] = what.text
    accident['stack'] = 'what_stack'


def parse_auxwhat(auxwhat, accident):
    accident['auxwhat'] = auxwhat.text
    accident['stack'] = 'auxwhat_stack'


def parse_stack(stack, accident):
    parse_fns = {
      'fn':   parse_fn,
      'dir':  parse_dir,
      'file': parse_file,
      'line': parse_line,
    }
    accident[accident['stack']] = []
    for xml_frame in stack:
        frame = Frame()
        for child in xml_frame:
            if child.tag in parse_fns:
                parse_fns[child.tag](child, frame)
        accident[accident['stack']].append(frame)


def parse_valgrind(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    parse_fns = {'kind':    parse_kind,
                 'what':    parse_what,
                 'auxwhat': parse_auxwhat,
                 'stack':   parse_stack,
                 }
    binary_id = None
    for user_comment in root.findall('usercomment'):
        binary_id = user_comment.text
    # exe_filename = None
    # for args_ in root.findall('args'):
    #     for argv_ in args_.findall('argv'):
    #         for exe_ in argv_.findall('exe'):
    #             exe_filename = exe_.text

    accidents = []

    for xml_accident in root.findall('error'):
        accident = {
            'stack': 'what_stack',
            'binary_id': binary_id,
        }
        for child in xml_accident:
            if child.tag in parse_fns:
                parse_fns[child.tag](child, accident)
        del accident['stack']
        accidents.append(accident)
    return accidents


def crash(accident):
    res = {'binary_id': accident['binary_id']}
    if 'kind' in accident:
        res['kind'] = accident['kind']
    if 'what' in accident:
        res['kind'] = accident['what']
    if 'what_stack' in accident:
        res['stack'] = []
        for frame in accident['what_stack']:
            res['stack'].append({
                'fn': frame.function,
                'file': frame.full_filename,
                'line': frame.line
            })
    annotation = []
    if 'auxwhat' in accident:
        annotation = [accident['auxwhat']]
    if 'auxwhat_stack' in accident:
        for frame in accident['auxwhat_stack']:
            annotation.append('  %s' % frame)
    res['annotation'] = '\n'.join(annotation)
    return res


def accidents_from_valgrind_log(filename):
    for valgrind_accident in parse_valgrind(filename):
        yield crash(valgrind_accident)
