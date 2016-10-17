"""
With the datapunt search api we can greatly improve
location quality of the datasets
"""
import re
import json
import string
import logging
import time
import requests

from django.conf import settings

import gevent
from gevent.queue import Queue
from gevent.queue import JoinableQueue


from django.contrib.gis.geos import GEOSGeometry
from .models import Locatie


searches = JoinableQueue(maxsize=5100)


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
wtflog = logging.getLogger('onbekent')
bag_error = logging.getLogger('bagerror')

if settings.DEBUG:
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
bag_error.setLevel(logging.DEBUG)

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
    """Find the index of the first number in the token string."""
    for i, token in enumerate(input_tokens):
        if token.isdigit():
            return i, token

    return -1, ""


def clean_tokenize(query_string):
    """
    Clean up query string and makes tokens.

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


def is_straat_huisnummer(tokens):
    """
    Check if unpunt contains a steer and number, return token index.
    """
    if len(tokens) < 2:
        return False

    i, _ = first_number(tokens)

    if i < 1:
        return False

    # wat is de kortste straat?
    if len("".join(tokens[:i])) > 2:
        return i


def get_details_for_vbo(straatnaam, nummer, num):
    """
    Get the detail of a specific verblijsobject
    """

    details_url = num['_links']['self']['href']
    details_request = requests.get(details_url)
    details = details_request.json()

    if details_request.status_code == 404:
        bag_error.debug("%s %s, %s", straatnaam, nummer, details_url)
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


def get_response(parameters):
    """
    Actualy do the http api search call
    """
    # log.debug(parameters)
    response = requests.get(search_adres_url, parameters)
    # Do something with the result count?
    return response.json()


def get_best_search_response(
        loc, query_string, straatnaam, nummer, toevoeging):
    """
    Given straatnaam , nummer and toevoeging try to find search
    result with only one result so we have an exact match
    """

    # Met toevoeging
    parameters_toevoeging = {
        'q': '{} {} {}'.format(straatnaam, nummer, toevoeging)
    }

    data = get_response(parameters_toevoeging)

    if not data['results']:
        # poging zonder toevoeging
        parameters = {'q': '{} {}'.format(straatnaam, nummer)}
        data = get_response(parameters)

    # print(data)

    if data.get('results'):
        return data

    # nothing found
    # save and log empty result result
    wtflog.debug('%s, %s, %s, %s', loc.id, straatnaam, nummer, query_string)
    loc.correctie = False
    loc.save()

    return []


def async_determine_rd_coordinates():

    while not searches.empty():
        args = searches.get()
        determine_rd_coordinates(*args)


def determine_rd_coordinates(
        loc, query_string, straatnaam, nummer, toevoeging):
    """
    Send adres requests to atlas to determine geo point and
    landelijk bag id of items

    If there is more then one hit try get more exact match
    with a search complete with 'toevoeging'
    """

    data = get_best_search_response(
        loc, query_string, straatnaam, nummer, toevoeging)

    if not data:
        return

    rds_bagid = []

    # Only do results with only 1 result?
    for num in data['results']:
        point, bag_id = get_details_for_vbo(straatnaam, nummer, num)
        if point:
            rds_bagid.append((point, bag_id))
            # The first point is enough
            break

    # print(rds)
    if rds_bagid:
        save_corrected_geo_infomation(
            loc, point, bag_id, straatnaam, nummer, toevoeging)
    else:
        return
        log.debug('Point/Bagid missing:', query_string)


def normalize_geo(point):
    """
    If we encounter a polygon. change it to point
    """

    if point['type'] == 'Point':
        return GEOSGeometry(json.dumps(point))
    elif point['type'] == 'Polygon':
        # create centroid from polygon (ligplaats)
        p = GEOSGeometry(json.dumps(point)).centroid
        return p.json


def save_corrected_geo_infomation(
        loc, point, bag_id, straat, nummer, toevoeging):
    """
    New adition location data is found, save it
    """
    loc.geometrie = normalize_geo(point)
    # we found a probably correct bag_id.
    # this is not 100% sure.
    # this is not 100% sure should we add bag_id?
    # how to handle this
    loc.bag_vbid = bag_id
    # we succesfull did a correction
    loc.correctie = True

    correctielog.debug('{}, {} {}, {}, {}, {}, {}'.format(
        loc.id,
        straat, nummer, toevoeging, bag_id,
        loc.geometrie[0],
        loc.geometrie[1],
    ))

    # save the new location
    loc.save()

    # update the stats
    STATS['correcties'] += 1


def improve_locations(qs):
    """
    For all items found in qs. Improve the location
    """

    log.debug('Finding incomplete adresses...')
    index = 0
    for loc in qs.iterator():

        addr = loc.volledig_adres

        # skip postbus items
        if addr.startswith('Postbus'):
            loc.correctie = False
            loc.save()
            continue

        query_string, tokens = clean_tokenize(addr)
        i = is_straat_huisnummer(tokens)

        straat = " ".join(tokens[:i])
        nummer = tokens[i]
        toevoeging = ""

        if len(tokens) > i:
            toevoeging = tokens[i+1][0]  # first character

        # add search tasks to queue
        while searches.full():
            gevent.sleep(1)

        searches.put((loc, query_string, straat, nummer, toevoeging))

        # log progress
        if index % 100 == 0:
            percentage = float(index) // STATS['total']
            log.debug('%s of %s - %s %%', index, STATS['total'], percentage)
        index += 1


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

        log.debug('Finding incomplete adresses...')

        count = qs.count()
        STATS['total'] = count
        print('\n Processing gemeente {} \n'.format(count))

        gevent.joinall([
            gevent.spawn(improve_locations, qs),
            gevent.spawn(async_determine_rd_coordinates),
            gevent.spawn(async_determine_rd_coordinates),
            gevent.spawn(async_determine_rd_coordinates),
            gevent.spawn(async_determine_rd_coordinates),
            gevent.spawn(async_determine_rd_coordinates),
            gevent.spawn(async_determine_rd_coordinates),
        ])
        # wait untill search queue is empty

        print(STATS['correcties'])
        STATS['correcties'] = 0
        print(time.time() - STATS['start'])
        break
