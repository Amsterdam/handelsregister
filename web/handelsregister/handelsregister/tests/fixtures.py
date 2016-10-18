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


def _search_fixtures_get(url, *args, **kwargs):

    for k, v in args[0].items():
        if 'q' in k:
            filename = '{}={}'.format(k, v)
            log.debug(filename)
            break

    if not filename:
        landelijk_id = url.split('/')[-1]
        filename = 'vbo={}'.format(landelijk_id)

    filename += '.json'

    res = requests.Response()
    res.encoding = "UTF-8"

    with open('{}/search_fixture_files/{}'.format(directory, filename), 'rb') as f:
        try:
            res._content = f.read()
            res.status_code = 200
        except FileNotFoundError:
            res.status_code = 404
            res._content = []

    return res


def patch_search_requests(f):
    """
    Decorator to patch the `requests` API to return files
    from the search_fixture_files directory.
    """
    return mock.patch('requests.get', _search_fixtures_get)(f)
