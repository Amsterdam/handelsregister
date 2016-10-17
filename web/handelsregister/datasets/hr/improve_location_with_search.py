"""
With the datapunt search api we can greatly improve
location quality of the datasets
"""
from django.contrib.gis.geos import GEOSGeometry

from .models import Locatie

import re
import json
import string
import requests
import logging
import time

import asyncio

q = asyncio.Queue()


STATS = dict(
    start=time.time(),
    correcties=0,
    onbekent=0
)

# set up some loggin of our corrections
# normal log
log = logging.getLogger(__name__)
# corrections log
correctielog = logging.getLogger('correcties')

# wtf logging
wtflog = logging.getLogger('onbekent')
bag_error = logging.getLogger('bagerror')

handler = logging.FileHandler('correcties.csv')
handler2 = logging.FileHandler('onbekent.csv')
handler3 = logging.FileHandler('bagerrors.csv')

formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)

correctielog.addHandler(handler)
wtflog.addHandler(handler2)
bag_error.addHandler(handler3)

correctielog.setLevel(logging.DEBUG)
wtflog.setLevel(logging.DEBUG)

search_adres_url = 'https://api-acc.datapunt.amsterdam.nl/search/adres/'


gemeenten = [
    'Amsterdam',
    'Amstelveen',
    'Diemen',
    'Ouder-Amstel',
    'Landsmeer',
    'Oostzaan',
    'Waterland',
    'Haarlemmerliede',
    'Haarlemmermeer',
    'Weesp',
    'Gooise Meren',
    'De Ronde Venen',
    'Purmerend',
    'Wormerland',
    'Velsen',
    'Haarlem',
    'Aalsmeer',
    'Stichtse Vecht',
    'Wijdemeren'
]

REPLACE_TABLE = "".maketrans(
    string.punctuation, len(string.punctuation)*" ")


def first_number(input_tokens):

    for i, token in enumerate(input_tokens):
        if token.isdigit():
            return i, token

    return -1, ""


def clean_tokenize(query_string):
    """
    Cleans up query string and makes tokens.

    - Replace puntuation with " " space.
    - Add space between numers and letters.
    - lowercase input

    Examples:

    6A
    ['6', 'A']

    'aaa bbb ccc'
    ['aaa', 'bbb', 'ccc']

    'add23b cd3df h-4'
    ['add', '23', 'b', 'cd', '3', 'df', 'h' '4']

    Nieuwe achtergracht 105-3 HA2
    ['Nieuwe', 'achtergracht', '105', '3', 'HA', '2']
    """
    # clear all wrong useless data

    tokens = []
    qs = query_string.translate(REPLACE_TABLE)
    qs = qs.lower()
    # split on digits and spaces
    tokens = re.findall('[^0-9 ]+|\\d+', qs)
    return qs, tokens


def is_straat_huisnummer(query_string, tokens):

    if len(tokens) < 2:
        return False

    i, num = first_number(tokens)

    if i < 1:
        return False

    # wat is de kortste straat?
    if len("".join(tokens[:i])) > 2:
        return i


def get_details_for_vbo(num):

    details_url = num['_links']['self']['href']
    details_request = requests.get(details_url)
    details = details_request.json()

    if details_request.status_code == 404:
        bag_error.debug(details_url)
        return None, None

    point = details['geometrie']

    # determine bag_id
    for key in ['verblijfsobjectidentificatie',
                'ligplaatsidentificatie',
                'standplaatsindentificatie']:
        bag_id = details.get(key)
        if bag_id:
            break

    return point, bag_id


def determine_rd_coordinates(
        loc, query_string, tokens,
        straatnaam, nummer, toevoeging):
    """
    Send adres requests to atlas to determine geo point and
    landelijk bag id of items

    If there is more then one hit try get more exact match
    with a search complete with 'toevoeging'
    """
    parameters = {
        'q': '{} {}'.format(straatnaam, nummer)
    }

    response = requests.get(search_adres_url, parameters)

    data = response.json()

    if not data['results']:
        wtflog.debug('{}, {}, {}, {}'.format(
            loc.id, straatnaam, nummer, query_string))
        loc.correctie = False
        loc.save()
        return None, None

    rds_bagid = []

    # only do results with only 1 result?
    for num in data['results']:
        point, bag_id = get_details_for_vbo(num)
        if point:
            rds_bagid.append((point, bag_id))
            # The first point is enough
            break

    # print(rds)
    if rds_bagid:
        return rds_bagid[0]
    else:
        return [None, None]
        log.debug('Point/Bagid missing:', query_string)


def normalize_geo(point):
    """
    If we encounter a polygon. change it to point
    """

    if point['type'] == 'Point':
        return GEOSGeometry(json.dumps(point))
    elif point['type'] == 'Polygon':
        # point['type'] = 'Point'
        # point['coordinates'] = point['coordinates'][0][0]
        print(point)
        p = GEOSGeometry(json.dumps(point)).centroid
        print(p.json)
        return p.json
        # return GEOSGeometry(json.dumps(point))


def save_corrected_geo_infomation(loc, point, bag_id, straat, nummer):
    """
    New data is found save it
    """
    loc.geometrie = normalize_geo(point)
    # should we add bag_id?
    loc.bag_vbid = bag_id
    loc.correctie = True

    correctielog.debug('{}, {} {}, {}, {}, {}'.format(
        loc.id,
        straat, nummer, bag_id,
        loc.geometrie[0],
        loc.geometrie[1],
    ))

    # save the new location
    loc.save()

    # update the stats
    STATS['correcties'] += 1


def improve_locations(qs):

    log.debug('missing geo {}'.format(qs.count()))

    for li, loc in enumerate(qs):

        addr = loc.volledig_adres

        # skip postbus items
        if addr.startswith('Postbus'):
            loc.correctie = False
            loc.save()
            continue

        query_string, tokens = clean_tokenize(addr)
        i = is_straat_huisnummer(query_string, tokens)

        straat = " ".join(tokens[:i])
        nummer = tokens[i]
        toevoeging = tokens[i+1]

        # find rd coordinate and bag_id
        point, bag_id = determine_rd_coordinates(
            loc, query_string, tokens,
            straat, nummer, toevoeging)

        # search gave us some rd coordinates...
        if point:
            save_corrected_geo_infomation(
                loc, point, bag_id, straat, nummer)

        # log progress
        if li % 100 == 0:
            log.debug('\n\n {} of {} - {} % \n'.format(
                      li, STATS['total'],
                      float(li) // STATS['total']))


def guess():
    """
    Do an search on street housenumber part of volledig adres and try to
    find geo_point
    """
    for gemeente in gemeenten:
        qs = Locatie.objects\
            .filter(geometrie__isnull=True) \
            .filter(volledig_adres__contains=gemeente) \
            .filter(correctie__isnull=True)

        count = qs.count()
        STATS['total'] = count
        print('\n Processing gemeente {} \n'.format(count))
        improve_locations(qs)
        print(STATS['correcties'])
        STATS['correcties'] = 0
        print(time.time() - STATS['start'])
        break
