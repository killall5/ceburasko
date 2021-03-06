import yaml
import urllib2
import os
from urlparse import urljoin


class UploadDataError(RuntimeError):
    pass


def upload_data(url, data, timeout=10):
    data = yaml.dump(data)
    request = urllib2.Request(url, data, {'Content-Type': 'application/x-yaml'})
    try:
        return urllib2.urlopen(request, timeout=timeout)
    except Exception as e:
        raise UploadDataError(e)


def upload_binary_info(version, ids, project_url, timeout=10):
    if project_url[-1] != '/':
        project_url += '/'
    url = os.path.join(project_url, './upload-binaries/')
    binary_info = {
        'version': version,
        'components': ids,
    }
    return upload_data(url, binary_info, timeout)


def upload_accidents(accidents, project_url, log_filenames=[], timeout=10):
    if project_url[-1] != '/':
        project_url += '/'
    binaries = {}
    known_kinds_url = urljoin(project_url, './known-kinds/')
    known_kinds = yaml.load(urllib2.urlopen(known_kinds_url, timeout=timeout))
    # regroup by binary_id
    for accident in accidents:
        if 'binary_id' not in accident:
            # skip unknown binary_id
            continue
        binary_id = accident['binary_id']
        del accident['binary_id']
        if 'kind' not in accident:
            # skip accidents without kind
            continue
        if accident['kind'] not in known_kinds:
            # skip unknown kinds
            continue
        accident['logs'] = log_filenames
        if binary_id not in binaries:
            binaries[binary_id] = [accident]
        else:
            binaries[binary_id].append(accident)
    payload = []
    for binary_id, accidents in binaries.items():
        binary_accidents = {
            'binary_id': binary_id,
            'accidents': accidents,
            'logs': {},
        }
        for filename in log_filenames:
            try:
                with open(filename) as log:
                    binary_accidents['logs'][filename] = log.read()
            except:
                pass
        payload.append(binary_accidents)
    url = urljoin(project_url, '../upload-accidents/')
    return upload_data(url, payload, timeout)
