"""
We use the objectstore to get the latest and greatest of the mks dump
"""

import os
import logging

from swiftclient.client import Connection

import datetime

from dateutil import parser

log = logging.getLogger('objectstore')

assert os.getenv('HANDELSREGISTER_OBJECTSTORE_PASSWORD')

OBJECTSTORE = dict(
    VERSION='2.0',
    AUTHURL='https://identity.stack.cloudvps.com/v2.0',
    TENANT_NAME='BGE000081_Handelsregister',
    TENANT_ID='0efc828b88584759893253f563b35f9b',
    USER=os.getenv('OBJECTSTORE_USER', 'handelsregister'),
    PASSWORD=os.getenv('HANDELSREGISTER_OBJECTSTORE_PASSWORD'),
    REGION_NAME='NL',
)


logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("swiftclient").setLevel(logging.WARNING)


DATA_DIR = 'data/'

store = OBJECTSTORE


EXPECTED_FILES = [
    'kvkadr.sql.gz',
    'kvkbeshdn.sql.gz',
    'kvkhdn.sql.gz',
    'kvkmac.sql.gz',
    'kvkprs.sql.gz',
    'kvkprsash.sql.gz',
    'kvkves.sql.gz',
    'kvkveshis.sql.gz',
]


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


def download_files(file_list):
    # Download the latest data
    for _, source_data_file in file_list:
        sql_gz_name = source_data_file['name'].split('/')[-1]
        msg = 'Downloading: %s' % (sql_gz_name)
        log.debug(msg)

        new_data = get_store_object(source_data_file)

        # save output to file!
        with open('data/{}'.format(sql_gz_name), 'wb') as outputzip:
            outputzip.write(new_data)


def get_latest_hr_files():
    """
    Download the expected files provided by mks / kpn
    """
    file_list = []

    meta_data = get_full_container_list(
        handelsregister_conn, 'handelsregister')

    for o_info in meta_data:
        for expected_file in EXPECTED_FILES:
            if o_info['name'].endswith(expected_file):
                dt = parser.parse(o_info['last_modified'])
                now = datetime.datetime.now()

                delta = now - dt

                log.debug('AGE: %d %s', delta.days, expected_file)

                if delta.days > 10:
                    log.error('DELEVERY IMPORTED FILES ARE TOO OLD!')
                    raise ValueError

                log.debug('%s %s', expected_file, dt)
                file_list.append((dt, o_info))

    download_files(file_list)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    get_latest_hr_files()
