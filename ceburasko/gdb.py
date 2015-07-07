import re
from subprocess import Popen, PIPE
from binary_id import binary_id_from_coredump, find_by_binary_id


def line_generator(data):
    out = ''
    for line in data:
        if line.startswith('#'):
            if out:
                yield out
            out = line
        else:
            out += ' ' + line
    if out:
        yield out


def parse_stack(data):
    sourced_line = re.compile('^#\d+ +(0x[0-9a-fA-F]+ in )?(?P<fn>.+) \([^)]*\) at (?P<file>[^=].*):(?P<line>\d+)')
    no_sourced_line = re.compile('^#\d+ +(0x[0-9a-fA-F]+ in )?(?P<fn>.+) \([^)]*\)')
    for line in line_generator(data):
        result = sourced_line.search(line)
        if result is None:
            result = no_sourced_line.search(line)
        yield result.groupdict()


def parse_gdb(input_stream):
    state = 0
    crash = {}
    for line in input_stream:
        line = line.strip()
        if state == 0:
            if line.startswith("Program terminated"):
                state = 1
                crash['kind'] = 'killed'
                crash['subtype'] = line
                continue
        if state == 1:
            crash['line'] = line
            state = 2
            continue
        if state == 2:
            if line == crash['line']:
                state = 3
                crash['data'] = []
                # do not continue!
        if state == 3:
            if line:
                crash['data'].append(line)
            else:
                crash['stack'] = list(parse_stack(crash['data']))
                del crash['data']
                del crash['line']
                yield crash
                state = 0
    if 'data' in crash:
        crash['stack'] = list(parse_stack(crash['data']))
        del crash['data']
        del crash['line']
        yield crash


def accident_from_coredump(coredump):
    try:
        binary_id = binary_id_from_coredump(coredump)
    except:
        return
    binary = find_by_binary_id(binary_id, cache='/var/cache/ceburasko/binary_id_cache.db')
    if not binary:
        return
    symbols = find_by_binary_id(binary_id, paths=['/usr/lib/debug'], cache='/var/cache/ceburasko/binary_id_symbols.db')
    if not symbols:
        return

    # TODO: get stack for all threads (bug in wheezy gdb?)
    gdb = Popen(["gdb", "--batch", "--quiet", "-ex", "bt full", "-ex", "quit", "--core", coredump, "--exec", binary, "--symbols", symbols], stdout=PIPE)
    annotation, _ = gdb.communicate()

    for accident in parse_gdb(annotation.split('\n')):
        accident['annotation'] = annotation
        accident['binary_id'] = binary_id
        yield accident
