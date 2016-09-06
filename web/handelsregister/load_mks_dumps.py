"""
We use the objectstore to get the latest and greatest
"""

import os
import logging
from swiftclient.client import Connection

from dateutil import parser

log = logging.getLogger(__name__)


OBJECTSTORE = dict(
    VERSION='2.0',
    AUTHURL='https://identity.stack.cloudvps.com/v2.0',
    TENANT_NAME='BGE000081_Handelsregister',
    TENANT_ID='0efc828b88584759893253f563b35f9b',
    USER=os.getenv('OBJECTSTORE_USER', 'handelsregister'),
    PASSWORD=os.getenv('OS_PASSWORD', 'insecure'),
    REGION_NAME='NL',
)


logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("swiftclient").setLevel(logging.WARNING)


DATA_DIR = 'data/'

store = OBJECTSTORE

handelsregister_conn = Connection(
    authurl=store['AUTHURL'],
    user=store['USER'],
    key=store['PASSWORD'],
    tenant_name=store['TENANT_NAME'],
    auth_version=store['VERSION'],
    os_options={'tenant_id': store['TENANT_ID'],
                'region_name': store['REGION_NAME']})


def get_store_object(object_meta_data):
    return handelsregister_conn.get_object(
        'handelsregister', object_meta_data['name'])[1]


def get_full_container_list(conn, container, **kwargs):
    limit = 10000
    kwargs['limit'] = limit
    page = []

    seed = []

    _, page = conn.get_container(container, **kwargs)
    seed.extend(page)

    while len(page) == limit:
        # keep getting pages..
        kwargs['marker'] = seed[-1]['name']
        _, page = conn.get_container(container, **kwargs)
        seed.extend(page)

    return seed


def get_latest_zipfile():
    """
    Get latest zipfile uploaded by mks
    """
    zip_list = []

    meta_data = get_full_container_list(
        handelsregister_conn, 'handelsregister')

    for o_info in meta_data:
        if o_info['content_type'] == 'application/zip':
            dt = parser.parse(o_info['last_modified'])
            zip_list.append((dt, o_info))

    zips_sorted_by_time = sorted(zip_list)

    time, object_meta_data = zips_sorted_by_time[-1]

    # Download the latest data
    zipname = object_meta_data['name'].split('/')[-1]
    log.info('Downloading: %s %s', time, zipname)

    latest_zip = get_store_object(object_meta_data)

    # save output to file!
    with open('data/{}'.format(zipname), 'wb') as outputzip:
        outputzip.write(latest_zip)

get_latest_zipfile()
