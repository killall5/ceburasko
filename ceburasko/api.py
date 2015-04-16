import yaml
import urllib2
import os
from urlparse import urljoin


def upload_data(url, data, timeout=10):
    data = yaml.dump(data)
    request = urllib2.Request(url, data, {'Content-Type': 'application/x-yaml'})
    return urllib2.urlopen(request, timeout=timeout)


def upload_binary_info(version, ids, project_url, timeout=10):
    if project_url[-1] != '/':
        project_url += '/'
    url = os.path.join(project_url, './upload-binaries/')
    binary_info = {
        'version': version,
        'components': ids,
    }
    return upload_data(url, binary_info, timeout)


def upload_accidents(accidents, project_url, timeout=10):
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
        if binary_id not in binaries:
            binaries[binary_id] = [accident]
        else:
            binaries[binary_id].append(accident)
    payload = []
    for binary_id, accidents in binaries.items():
        payload.append({
            'binary_id': binary_id,
            'accidents': accidents,
        })
    url = urljoin(project_url, '../upload-accidents/')
    return upload_data(url, payload, timeout)
