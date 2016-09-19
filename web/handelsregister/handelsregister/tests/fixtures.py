import os
import logging
import requests

from unittest import mock
directory = os.path.dirname(__file__)


log = logging.getLogger(__name__)


def _filter_fixtures_get(url, *args, **kwargs):
    """
    Derive from parameters of 'request.get'
    function which json filename
    we need.
    """

    for k, v in args[0].items():
        if '_id' in k:
            filename = '{}={}'.format(k, v)
            break

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
