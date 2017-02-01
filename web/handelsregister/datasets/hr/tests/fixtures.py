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
    fixturefiles = {'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/Sections': 'cbs_sbi_sections.json',
                    'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/M': 'cbs_sbi_sectiontree_M.json',
                    'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/R': 'cbs_sbi_sectiontree_R.json',
                    'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/T': 'cbs_sbi_sectiontree_T.json',
                    'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/N': 'cbs_sbi_sectiontree_N.json'
    }
    try:
        filename = fixturefiles[url]
    except:
        filename = 'notfound'

    res = requests.Response()
    res.encoding = "UTF-8"

    try:
        with open('{}/fixture_files/{}'.format(directory, filename), 'rb') as f:
            res._content = f.read()
            res.status_code = 200
    except FileNotFoundError:
        res.status_code = 400

    return res


def patch_cbs_requests(f):
    """
    Decorator to patch the `requests` API to return files
    from the fixture_files directory.
    """
    return mock.patch('requests.get', _filter_fixtures_get)(f)

