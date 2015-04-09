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
    url = os.path.join(project_url, 'upload-crash/')
    for error in errors:
        upload_data(url, error)
