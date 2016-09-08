import os
from unittest import mock

import requests

directory = os.path.dirname(__file__)


def _filter_fixtures_get(url, *args, **kwargs):

    filename = url.split('?')[1]

    filename += '.json'

    res = requests.Response()
    res.encoding = "UTF-8"

    with open('{}/fixture_files/{}'.format(directory, filename), 'rb') as f:
        try:
            res._content = f.read()
            res.status_code = 200
        except FileNotFoundError:
            res.status_code = 400
    return res


def patch_filter_requests(f):
    """
    Decorator to patch the `requests` API to return files
    from the fixture_files directory.
    """
    return mock.patch('requests.get', _filter_fixtures_get)(f)
