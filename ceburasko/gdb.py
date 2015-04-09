import re

def parse_stack(data):
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

    sourced_line = re.compile('^#\d+ +(0x[0-9a-fA-F]+ in )?(?P<fn>.+) \([^)]*\) at (?P<file>[^=].*):(?P<line>\d+)')
    no_sourced_line = re.compile('^#\d+ +(0x[0-9a-fA-F]+ in )?(?P<fn>.+) \([^)]*\)')
    for line in line_generator(data):
        result = sourced_line.search(line)
        if result is None:
            result = no_sourced_line.search(line)
        yield result.groupdict()

def parse_gdb(istream):
    res = {}
    state = 0
    crash = {}
    pattern = re.compile(' +\([^)]*\)?( at .+)?$')
    for line in istream:
        if state == 0:
            if line.startswith("Program terminated"):
                state = 1
                crash['kind'] = line
                continue
        if state == 1:
            crash['line'] = line
            state = 2
            continue
        if state == 2:
            if len(line) == 0:
                state = 3
            continue
        if state == 3:
            if line == crash['line']:
                state = 4
                crash['data'] = []
                # do not continue!
        if state == 4:
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

def errors_from_gdb_log(filename):
    with open(filename) as f:
        log = f.read().split('\n')

    exe_id = None
    try:
        ind = log.index('end-of-exe-id.')
        if ind > 0:
            exe_id = log[0].split()[0]
        log = log[ind+1:]
    except:
        # gdb log must be prepended with exe ids
        return

    annotation = '\n'.join(log)
    for error in parse_gdb(log):
        error['annotation'] = annotation
        if exe_id:
            error['exe_id'] = exe_id
        yield error
