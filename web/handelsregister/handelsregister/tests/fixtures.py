import os
import logging
import requests

from unittest import mock

DIRECTORY = os.path.dirname(__file__)


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

    try:
        with open('{}/fixture_files/{}'.format(DIRECTORY, filename), 'rb') as f:
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


def set_response_with_fixture_file(res, filename):

    try:
        with open('{}/search_fixture_files/{}'.format(DIRECTORY, filename), 'rb') as f:
            res._content = f.read()
            res.status_code = 200
    except FileNotFoundError:
        res.status_code = 404


def _search_fixtures_get(url, *args, **kwargs):

    filename = None
    res = requests.Response()

    log.debug(url)

    try:
        q = kwargs['params']['q']
        filename = 'q={}'.format(q)
    except (KeyError, TypeError):
        pass

    if not filename:
        landelijk_id = url.split('/')[-2]
        filename = 'vbo={}'.format(landelijk_id)

    log.debug(filename)

    filename += '.json'

    res.encoding = "UTF-8"

    if filename:
        set_response_with_fixture_file(res, filename)

    class AsyncObject():
        """ mock async get request"""

        def __init__(self, response):
            self.response = res

        def send(self):
            pass

    return AsyncObject(res)


def patch_search_requests(f):
    """
    Decorator to patch the `requests` API to return files
    from the search_fixture_files directory.
    """
    return mock.patch('grequests.get', _search_fixtures_get)(f)
