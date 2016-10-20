"""
With the datapunt search api we can greatly improve
location quality of the datasets
"""
import re
import json
import string
import logging
import time

from requests import Session

import grequests

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

import gevent
from gevent.queue import JoinableQueue


from .models import Locatie

log = logging.getLogger(__name__)

SEARCHES_QUEUE = JoinableQueue(maxsize=500)


STATS = dict(
    start=time.time(),
    correcties=0,
    onbekend=0
)

# the amount of concurrent workers that do requests
# to the search api
WORKERS = 1


class CSVLOGHANDLER():
    """
    set up some loggin of our corrections
    normal log
    log corrected output to a csv file

    """
    # corrections log
    correctie = logging.getLogger('correcties')
    wtf = logging.getLogger('onbekend')
    bag_error = logging.getLogger('bagerror')

    def __init__(self):
        if settings.DEBUG:

            csvfiles = [
                (self.correctie, 'correcties.csv'),
                (self.wtf, 'onbekend.csv'),
                (self.bag_error, 'bagerrors.csv')
            ]
            for csvlogger, csvf in csvfiles:
                handler = logging.FileHandler(csvf)
                handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(message)s')
                handler.setFormatter(formatter)
                csvlogger.addHandler(handler)
        else:
            # Disable logging on screen
            self.correctie.setLevel(logging.CRITICAL)
            self.wtf.setLevel(logging.CRITICAL)
            self.bag_error.setLevel(logging.CRITICAL)

CSV = CSVLOGHANDLER()

SEARCH_ADRES_URL = 'https://api-acc.datapunt.amsterdam.nl/search/adres/'


GEMEENTEN = [
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


def first_house_number(input_tokens):
    """Find the index of the first number in the token string."""

    for i, token in enumerate(input_tokens):
        # skip (1e , 2e, 3e blabla street)
        if i and token.isdigit():
            return i, token

    return -1, ""


def alternative_qs(query_string):
    """
    Create common alternatives.
    for patterns
    """
    alternatives = [query_string]

    could_also_be = [
        ("1e", "eerste"),
        ("2e", "tweede"),
        ("3e", "derde"),
        ("4e", "vierde"),
        ("5e", "vijfde"),
    ]

    for patern, replace in could_also_be:
        if query_string.startswith(patern):
            qs_new = query_string.replace(patern, replace)
            alternatives.append(qs_new)

    return alternatives

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
    query_string = query_string.translate(REPLACE_TABLE)
    query_string = query_string.lower()

    # split on digits and spaces
    tokens = re.findall('[^0-9 ]+|\\d+', query_string)
    return query_string, tokens


def is_straat_huisnummer(tokens):
    """
    Check if unpunt contains a steer and number, return token index.
    """
    if len(tokens) < 2:
        return False

    i, _ = first_house_number(tokens)

    if i < 1:
        return False

    # wat is de kortste straat?
    if len("".join(tokens[:i])) > 2:
        return i


class SearchTask():
    """
    All data relevant for async search instance
    We get raw 'volledig_adres' and try to ind

    """

    def __init__(self, locatieobject, query_string, straatnaam,
                 nummer, toevoeging):

        self.locatie = locatieobject
        # originele input
        self.query_string = query_string
        # found straatnaam
        self.straatnaam = straatnaam
        # found huisnummer
        self.nummer = nummer
        # found toevoeging
        self.toevoeging = toevoeging
        # no search hit found then try without tovoeging
        self.use_toevoeging = True

        # corrected bag_id for this
        self.bag_id = None
        # corrected geometrie
        self.geometrie = None
        # http session
        self.session = Session()

    def get_response(self, parameters):
        """
        Actualy do the http api search call
        """
        # parameters = {'q': self.get_q()}
        async_r = grequests.get(SEARCH_ADRES_URL, params=parameters, session=self.session)
        # send a request and wait for results
        gevent.spawn(async_r.send).join()
        # Do something with the result count?

        if not async_r.response:
            return {}
        elif async_r.response.status_code == 404:
            log.error(parameters)
            return {}

        return async_r.response.json()


    def determine_rd_coordinates(self):
        """
        Send adres requests to atlas to determine geo point and
        landelijk bag id of items

        If there is more then one hit try get more exact match
        with a search complete with 'toevoeging'
        """

        data = self.get_exact_search_response()
        self.locatie.refresh_from_db()

        # check if locatie is already fixed.
        if self.locatie.correctie is True:
            return

        if not data:
            # nothing found return
            return

        rds_bagid = []

        # We Only do results with 1 result.
        num = data['results'][0]
        point, bag_id = self.get_details_for_vbo(num)
        if point:
            rds_bagid.append((point, bag_id))
            # The first point is enough
        if rds_bagid:
            self.save_corrected_geo_infomation(point, bag_id)
        else:
            log.debug('Point/Bagid missing: %s', self.get_q())
            return

    def get_q(self):
        """
        Create query string for search
        """
        if self.use_toevoeging:
            return '{} {} {}'.format(
                self.straatnaam,
                self.nummer, self.toevoeging)

        return '{} {}'.format(self.straatnaam, self.nummer)

    def do_geo_fix(self, data):
        """
        Do a geometrie fix
        """
        pass

    def get_exact_search_response(self):
        """
        Given straatnaam , nummer and toevoeging try to
        find exact search result with
        only one result so we have an exact match
        """

        # First with toevoeging
        parameters_toevoeging = {'q': self.get_q()}
        data = self.get_response(parameters_toevoeging)

        # Only if we are realy sure we return data
        if data and data.get('results') and data['count'] == 1:
            return data

        if data and data.get('results'):
            self.do_geo_fix(data)
            return []

        self.locatie.refresh_from_db()
        # Check if locatie is already fixed.
        if self.locatie.correctie is True:
            # already fixed!
            return []

        # Correctie failed
        # save and log empty result result
        self.locatie.correctie = False
        self.locatie.save()

        self.log_wtf_loc()

        return []

    def log_wtf_loc(self):
        """
        nothing found
        """
        CSV.wtf.debug(
            '%s, %s, %s, %s, %s',
            self.locatie.id,
            self.straatnaam,
            self.nummer,
            self.toevoeging,
            self.query_string)

    def get_details_for_vbo(self, num):
        """
        Get the detail of a specific verblijsobject
        """

        details_url = num['_links']['self']['href']
        details_request = grequests.get(details_url, session=self.session)
        gevent.spawn(details_request.send).join()
        details_request = details_request.response

        if details_request.status_code == 404:
            CSV.bag_error.debug("%s, %s", self.get_q(), details_url)
            return None, None

        details = details_request.json()

        point = details['geometrie']

        # determine bag_id
        for key in ['verblijfsobjectidentificatie',
                    'ligplaatsidentificatie',
                    'standplaatsindentificatie']:
            bag_id = details.get(key)
            if bag_id:
                break

        return point, bag_id

    def save_corrected_geo_infomation(self, point, bag_id):
        """
        New adition location data is found, save it
        """
        geometrie = normalize_geo(point)
        self.locatie.geometrie = geometrie

        self.geometrie = geometrie

        # we found a probably correct bag_id.
        # this is not 100% sure.
        # this is not 100% sure should we add bag_id?
        # how to handle this
        self.locatie.bag_vbid = bag_id
        self.bag_id = bag_id

        locatie = self.locatie
        # we succesfull did a correction
        locatie.correctie = True

        logmessage = '{}, {}, {}'.format(
            locatie.id,
            self.get_q(),
            bag_id,
        )
        CSV.correctie.debug(logmessage)

        # save the new location
        locatie.save()

        # update the stats
        STATS['correcties'] += 1



def async_determine_rd_coordinates():
    """
    Worker task which gets
    search parameters of the queue
    and executes a SearchTask
    """

    while not SEARCHES_QUEUE.empty():
        args = SEARCHES_QUEUE.get()
        task = SearchTask(*args)
        task.determine_rd_coordinates()


def normalize_geo(point):
    """
    If we encounter a polygon. change it to point
    """

    if point['type'] == 'Point':
        return GEOSGeometry(json.dumps(point))
    elif point['type'] == 'Polygon':
        # create centroid from polygon (ligplaats)
        centroid_p = GEOSGeometry(json.dumps(point)).centroid
        return centroid_p.json


def normalize_toevoeging(toevoeging):
    """
    fix toevoeging indicaties
    """
    toevoeging = toevoeging.lower()

    alternativen = [toevoeging]

    begane_grond = ['H', 1, 'A', 'O']
    mapping = {
        '1hg': [1],
        '2hg': [2],
        '3hg': [3],
        'iii': [3],
        'ii': [2],
        'A': begane_grond,
        'bg': begane_grond,
        'i': begane_grond,
        'huis': begane_grond,
        'hs': begane_grond,
        'sous': begane_grond,
        'bel': begane_grond,
        'parterre': begane_grond
    }

    if toevoeging in mapping:
        alternativen.extend(mapping[toevoeging])

    return alternativen


def create_improve_locations_tasks(all_invalid_locations):
    """
    For all items found in qs. Improve the location
    and start tasks by specifying search tasks that will
    likely match with ONE !! specific adres
    """

    log.debug('Finding incomplete adresses...')
    index = 0
    for loc in all_invalid_locations.iterator():

        addr = loc.volledig_adres

        # skip postbus items
        if addr.startswith('Postbus'):
            loc.correctie = False
            loc.save()
            continue

        # figure out with adresses could be alternative
        for alternative_addr in alternative_qs(addr):
            create_search_for_addr(loc, alternative_addr)

        # log progress
        if index % 100 == 0:
            percentage = (float(index) // STATS['total']) * 100
            log.debug('%s of %s - %.2f %%', index, STATS['total'], percentage)

        index += 1


def create_search_for_addr(loc, addr):
    """
    Create search tasks for specific adres
    """
    query_string, tokens = clean_tokenize(addr)
    i = is_straat_huisnummer(tokens)

    straat = " ".join(tokens[:i])
    nummer = tokens[i]
    toevoeging = [""]

    if not straat:
        loc.correctie = False
        loc.save()
        log.error(addr)
        return

    if len(tokens) > i:
        toevoeging = tokens[i+1]
        # fix common toevoeging mistakes
        toevoeging = normalize_toevoeging(toevoeging)
        # print(toevoeging)

    # add search tasks to queue
    while SEARCHES_QUEUE.full():
        gevent.sleep(2.3)

    for try_t in toevoeging:
        SEARCHES_QUEUE.put((loc, query_string, straat, nummer, try_t))

    # search also with empty toevoeging
    SEARCHES_QUEUE.put((loc, query_string, straat, nummer, ''))


def create_qs_of_invalid_locations(gemeente):
    """
    Create a qs of invalid locations.

    - Invalid are locations with no geomatrie,
    - Having an adres withing 'gemeente'
    - No correction has been attempted
    """

    return Locatie.objects\
            .filter(geometrie__isnull=True) \
            .filter(volledig_adres__endswith=gemeente) \
            .filter(correctie__isnull=True)


def guess():
    """
    Do an search on street housenumber part of volledig adres and try to
    find geo_point
    """
    log.debug('Start Finding and correcting incomplete adresses...')

    for gemeente in GEMEENTEN:
        invalid_locations = create_qs_of_invalid_locations(gemeente)

        count = invalid_locations.count()

        if count == 0:
            continue

        STATS['total'] = count
        print('\n Processing gemeente {} {} \n'.format(gemeente, count))

        jobs = [gevent.spawn(
            create_improve_locations_tasks, invalid_locations)]

        for _ in range(WORKERS):
            jobs.append(
                gevent.spawn(async_determine_rd_coordinates))

        # waint untill all search tasks are done
        gevent.joinall(jobs)

        # store corrections for each gemeente
        STATS[gemeente] = STATS['correcties']

        log.debug('\nCorrecties %s Duration %i seconds\n',
                  STATS['correcties'], time.time() - STATS['start'])

        # reset correcties count
        STATS['correcties'] = 0

    # log end result
    for gemeente in GEMEENTEN:
        if not gemeente in STATS:
            continue
        log.debug('%s - correcties: %s', gemeente, STATS[gemeente])

    total_seconds = time.time() - STATS['start']
    log.debug('\nTotal Duration %i m: %i\n', total_seconds / 60.0, total_seconds % 60)
