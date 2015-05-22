from subprocess import Popen, PIPE


class MinidumpError(RuntimeError):
    pass


def parse_minidump(input_stream):
    state = 0
    crash = {'ids': [], 'stack': []}
    for line in input_stream:
        line = line.strip()
        fields = line.split('|')
        if not line:
            if state == 0:
                state = 1
            continue
        if state == 0:
            if fields[0] == 'Crash':
                if fields[1] == 'DUMP_REQUESTED':
                    crash['kind'] = 'dump'
                else:
                    crash['kind'] = 'killed'
                crash['subtype'] = fields[1]
                crash['thread'] = fields[3]
            if fields[0] == 'Module':
                crash['ids'].append('breakpad:%s' % fields[4])
        elif state == 1:
            if fields[0] == crash['thread']:
                frame = {}
                if fields[3]:
                    frame['fn'] = fields[3]
                if fields[4]:
                    frame['file'] = fields[4]
                if fields[5]:
                    frame['line'] = fields[5]
                crash['stack'].append(frame)
    del crash['thread']
    if crash['stack']:
        yield crash

def accident_from_minidump(minidump_filename, symbols_dir):
    stackwalk = Popen(['minidump_stackwalk', '-m', minidump_filename, symbols_dir], stdout=PIPE)
    stackwalk_output, _ = stackwalk.communicate()
    if stackwalk.wait() != 0:
        raise MinidumpError('minidump_stackwalk failed with return code %d', stackwalk.wait())

    for accident in parse_minidump(stackwalk_output.split('\n')):
        yield accident
