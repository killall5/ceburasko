import yaml
import urllib2
import os


def upload_data(url, data, timeout=10):
    data = yaml.dump(data)
    request = urllib2.Request(url, data, {'Content-Type': 'application/x-yaml'})
    return urllib2.urlopen(request, timeout=timeout)


def upload_binary_info(version, ids, project_url):
    url = os.path.join(project_url, 'upload-binaries/')
    binary_info = {
        'version': version,
        'components': ids,
    }
    return upload_data(url, binary_info)


def upload_errors(errors, project_url):
    binaries = {}
    # regroup by binary_id
    for error in errors:
        if 'binary_id' not in error:
            # skip unknown binary_id
            continue
        binary_id = error['binary_id']
        del error['binary_id']
        if binary_id not in binaries:
            binaries[binary_id] = [error]
        else:
            binaries[binary_id].append(error)
    payload = []
    for binary_id, accidents in binaries.items():
        payload.append({
            'binary_id': binary_id,
            'accidents': accidents,
        })
    url = os.path.join(project_url, 'upload-crash/')
    return upload_data(url, payload)