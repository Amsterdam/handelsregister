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
    onbekent=0
)


class CSVLOGHANDLER():
    """
    set up some loggin of our corrections
    normal log
    log corrected output to a csv file

    """
    # corrections log
    correctie = logging.getLogger('correcties')
    wtf = logging.getLogger('onbekent')
    bag_error = logging.getLogger('bagerror')

    def __init__(self):
        if settings.DEBUG:

            csvfiles = [
                (self.correctie, 'correcties.csv'),
                (self.wtf, 'onbekent.csv'),
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

    i, _ = first_number(tokens)

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
        return async_r.response.json()


    def determine_rd_coordinates(self):
        """
        Send adres requests to atlas to determine geo point and
        landelijk bag id of items

        If there is more then one hit try get more exact match
        with a search complete with 'toevoeging'
        """

        data = self.get_best_search_response()

        if not data:
            return

        rds_bagid = []

        # Only do results with only 1 result?
        for num in data['results']:
            point, bag_id = self.get_details_for_vbo(num)
            if point:
                rds_bagid.append((point, bag_id))
                # The first point is enough
                break

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

    def get_best_search_response(self):
        """
        Given straatnaam , nummer and toevoeging try to find search
        result with only one result so we have an exact match
        """

        # First with toevoeging
        parameters_toevoeging = {'q': self.get_q()}
        data = self.get_response(parameters_toevoeging)
        # Als niets is gevonden dan zonder toevoeging
        if not data:
            # poging zonder toevoeging
            self.use_toevoeging = False
            parameters = {'q': self.get_q()}
            data = self.get_response(parameters)

        if data and data.get('results'):
            return data

        # nothing found
        # save and log empty result result
        CSV.wtf.debug(
            '%s, %s, %s, %s',
            self.locatie.id,
            self.straatnaam,
            self.nummer,
            self.query_string)

        self.locatie.correctie = False
        self.locatie.save()

        return []

    def get_details_for_vbo(self, num):
        """
        Get the detail of a specific verblijsobject
        """

        details_url = num['_links']['self']['href']
        details_request = grequests.get(details_url, session=self.session)
        gevent.spawn(details_request.send).join()
        details_request = details_request.response
        details = details_request.json()

        if details_request.status_code == 404:
            CSV.bag_error.debug("%s, %s", self.get_q(), details_url)
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

        logmessage = '{}, {}, {}, {}, {}'.format(
            locatie.id,
            self.get_q(),
            bag_id,
            geometrie[0],
            geometrie[1]
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
        p = GEOSGeometry(json.dumps(point)).centroid
        return p.json


def create_improve_locations_tasks(all_invalid_locations):
    """
    For all items found in qs. Improve the location
    and start tasks
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

        query_string, tokens = clean_tokenize(addr)
        i = is_straat_huisnummer(tokens)

        straat = " ".join(tokens[:i])
        nummer = tokens[i]
        toevoeging = ""

        if len(tokens) > i:
            toevoeging = tokens[i+1][0]  # first character

        # add search tasks to queue
        while SEARCHES_QUEUE.full():
            gevent.sleep(2.3)

        SEARCHES_QUEUE.put((loc, query_string, straat, nummer, toevoeging))

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
    for gemeente in GEMEENTEN:
        invalid_locations = Locatie.objects\
            .filter(geometrie__isnull=True) \
            .filter(volledig_adres__endswith=gemeente) \
            .filter(correctie__isnull=True) \

        log.debug('Finding incomplete adresses...')

        count = invalid_locations.count()
        STATS['total'] = count
        print('\n Processing gemeente {} {} \n'.format(gemeente, count))

        jobs = [gevent.spawn(
            create_improve_locations_tasks, invalid_locations[:100])]

        for _ in range(12):
            jobs.append(
                gevent.spawn(async_determine_rd_coordinates))

        gevent.joinall(jobs)
        # wait untill search queue is empty

        print(STATS['correcties'])
        STATS[gemeente] = STATS['correcties']

        log.debug('\nCorrecties %s Duration %i seconds\n',
            STATS['correcties'], time.time() - STATS['start'])

        STATS['correcties'] = 0

    for gemeente in GEMEENTEN:
        log.debug('%s - correcties: %s', gemeente, STATS[gemeente])

    total_seconds = time.time() - STATS['start']
    log.debug('\nTotal Duration %i m: %i\n', total_seconds / 60.0, total_seconds % 60)
