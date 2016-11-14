"""
With the datapunt search api we can greatly improve
location quality of the datasets
"""

from gevent import monkey
monkey.patch_all(thread=False, select=False)


import datetime
import re
import json
import string
import sys
import logging
import time

from collections import OrderedDict

from requests import Session

import grequests

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

import gevent
from gevent.queue import JoinableQueue


from .models import Locatie

log = logging.getLogger(__name__)

SEARCHES_QUEUE = JoinableQueue(maxsize=500)

# TO see step by step what search does.
SLOW = False
#SLOW = True

STATS = dict(
    start=time.time(),
    correcties=0,
    onbekend=0,
    total=50,  # prevent by zero errors
    reqs=0,
    left=0,
)

# the amount of concurrent workers that do requests
# to the search api
WORKERS = 15
if SLOW:
    WORKERS = 1  # 25

SEARCH_ADRES_URL = 'https://api-acc.datapunt.amsterdam.nl/search/adres/'
NUM_URL = "https://api-acc.datapunt.amsterdam.nl/bag/nummeraanduiding/{}/"
VBO_URL = "https://api-acc.datapunt.amsterdam.nl/bag/verblijfsobject/{}/"


def make_status_line():
    status_line = 'All %s fixed: %s  ?: %s  req/s %s  left: %s \r'
    complete_status_line = status_line % (
        STATS['total'],
        STATS['correcties'],
        STATS['onbekend'],
        STATS['reqs'],
        STATS['left']
    )
    return complete_status_line


def req_counter():
    """
    Get an indication of the request per second
    """
    interval = 3.0
    if SLOW:
        interval = 30

    while True:
        start = STATS['correcties']
        gevent.sleep(interval)
        diff = STATS['correcties'] - start + 0.001
        speed = (diff // interval) + 1
        STATS['reqs'] = '%.2f' % speed
        seconds_left = abs(STATS['total'] + 1) // speed
        STATS['left'] = datetime.timedelta(seconds=seconds_left)
        log.info(make_status_line())


class CSVLOGHANDLER():
    """
    set up some logging
    """
    wtf = logging.getLogger('onbekend')
    bag_error = logging.getLogger('bagerror')

    def __init__(self):
        if not settings.DEBUG:
            self.wtf.setLevel(logging.CRITICAL)
            self.bag_error.setLevel(logging.CRITICAL)

CSV = CSVLOGHANDLER()


# we corrigeren alleen voor Amsterdam.
# search doet nog geen postcode controle
# of woonplaats controle bij een suggestie.

GEMEENTEN = [
    'Amsterdam',
    # 'Amstelveen',
    # 'Diemen',
    # 'Ouder-Amstel',
    # 'Landsmeer',
    # 'Oostzaan',
    # 'Waterland',
    # 'Haarlemmerliede',
    # 'Haarlemmermeer',
    # 'Weesp',
    # 'Gooise Meren',
    # 'De Ronde Venen',
    # 'Purmerend',
    # 'Wormerland',
    # 'Velsen',
    # 'Haarlem',
    # 'Aalsmeer',
    # 'Stichtse Vecht',
    # 'Wijdemeren'
]

REPLACE_TABLE = "".maketrans(
    string.punctuation, len(string.punctuation)*" ")


def first_house_number(input_tokens):
    """Find the index of the first number in the token string."""

    for i, token in enumerate(input_tokens):
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
                 nummers, toevoegingen, postcode):

        self.locatie = locatieobject
        # originele input
        self.query_string = query_string
        # found straatnaam
        self.straatnaam = straatnaam
        # found huisnummer
        self.nummers = nummers
        # found toevoeging
        self.toevoegingen = toevoegingen
        self.postcode = postcode

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
        async_r = grequests.get(
            SEARCH_ADRES_URL, params=parameters, session=self.session)
        # send a request and wait for results

        job = gevent.spawn(async_r.send)
        job.join()
        # Do something with the result count?

        async_r = job.value

        if not async_r:
            log.debug('no response')
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
        with a search complete with 'toevoegingen'
        """

        data = self.get_exact_search_response()

        if not data:
            # nothing found return
            # is already logged.
            return

        rds_bagid = []

        # We Only deal with first results.
        num = data['results'][0]
        # TODO Get and check POSTCODE from nummer aanduiding!
        point, bag_id, num_id = self.get_details_for_vbo(num)

        if point:
            rds_bagid.append((point, bag_id))
            # The first point is enough
        if rds_bagid:
            self.save_corrected_geo_infomation(point, bag_id, num_id)
        else:
            log.debug('Point/Bagid missing: %s', self.get_q())
            return

    def get_q(self, toevoeging, nummer=None, postcode=None):
        """
        Create query string for search
        """
        if not nummer:
            nummer = self.nummers[0]

        if postcode:
            return '{} {} {}'.format(
                 self.postcode, nummer, toevoeging)

        return '{} {} {}'.format(
            self.straatnaam, nummer, toevoeging)

    def do_one_hit(self, qs_try):
        # straat/postcode huisnummer toevoeging
        parameters_toevoeging = {'q': qs_try}

        data = self.get_response(parameters_toevoeging)

        # Only if we are realy sure we return data
        # FIXME postcode check!
        if SLOW:
            count = 0
            if data:
                count = data.get('count', 0)
            log.debug('q=%s hits=%s', qs_try, count)

        if data and data.get('results') and data['count'] == 1:
            self.used_query_string = qs_try
            return data

    def get_exact_search_response(self):
        """
        Given straatnaam , nummer and toevoeging try to
        find exact search result with
        only one result so we have an exact match
        """
        data = None

        # First with toevoeging
        for nummer in self.nummers:
            for t in self.toevoegingen:

                if self.postcode:
                    # postcode nummmer toevoeging
                    qs_try = self.get_q(
                        t, nummer=nummer, postcode=self.postcode)
                    data = self.do_one_hit(qs_try)

                if SLOW:
                    gevent.sleep(0.5)

                if not data:
                    # straatnaam nummer toevoeging
                    qs_try = self.get_q(t, nummer=nummer)
                    data = self.do_one_hit(qs_try)

                if SLOW:
                    gevent.sleep(0.5)

                if data:
                    return data

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
            '%s, %s, %s, %s, %s, %s',
            self.locatie.id,
            self.straatnaam,
            self.postcode,
            self.nummers,
            self.toevoegingen,
            self.query_string)

        STATS['onbekend'] += 1

    def get_details_for_vbo(self, num):
        """
        Get the detail of a specific verblijsobject
        """

        details_url = num['_links']['self']['href']
        details_request = grequests.get(details_url, session=self.session)
        gevent.spawn(details_request.send).join()
        details_request = details_request.response

        if not details_request or details_request.status_code == 404:
            CSV.bag_error.debug("%s, %s", self.get_q(), details_url)
            return None, None

        details = details_request.json()

        point = details['geometrie']
        num_id = None
        if details['hoofdadres']:
            num_id = details['hoofdadres'].get("landelijk_id")

        # determine bag_id
        for key in ['verblijfsobjectidentificatie',
                    'ligplaatsidentificatie',
                    'standplaatsindentificatie']:
            bag_id = details.get(key)
            if bag_id:
                break
        return point, bag_id, num_id

    def save_corrected_geo_infomation(self, point, bag_id, num_id):
        """
        New adition location data is found, save it
        """
        geometrie = normalize_geo(point)
        self.locatie.geometrie = geometrie
        self.geometrie = geometrie

        # we found a probably correct bag_id.
        # this is not 100% sure.
        self.locatie.bag_vbid = bag_id
        self.locatie.bag_numid = num_id
        self.locatie.bag_nummeraanduiding = NUM_URL.format(num_id)
        self.locatie.bag_adresseerbaar_object = VBO_URL.format(bag_id)

        self.bag_id = bag_id

        locatie = self.locatie
        # we succesfull did a correction
        locatie.correctie = True
        locatie.query_string = self.used_query_string

        # save the new location
        locatie.save()

        # update the stats
        STATS['correcties'] += 1

        if settings.DEBUG:
            sys.stdout.write(make_status_line())
            sys.stdout.flush()


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


BEGANE_GROND = set(['H', 1, 'A', 'O'])


def normalize_toevoeging(toevoegingen=[""]):
    """
    zoek toevoeging indicaties
    en alle alternativen
    """

    toevoegingen = [t.lower() for t in toevoegingen]
    alternatieven = ["".join(toevoegingen)]

    # generete from specific to less specific alternatives for
    # toevoegingen
    for i in reversed(range(len(toevoegingen))):
        optie = "".join(toevoegingen[:i])
        alternatieven.append(optie)

    begane_grond = BEGANE_GROND

    mapping = {
        '1hg': [1, 2],
        '2hg': [2, 3],
        '3hg': [3, 4],
        'iii': [3],
        'ii': [2],
        'i': begane_grond,
        'a': begane_grond,
        'b': [1, 2],
        'bg': begane_grond,
        'huis': begane_grond,
        'hs': begane_grond,
        'sous': begane_grond,
        'bel': begane_grond,
        'parterre': begane_grond
    }
    for toevoeging in list(alternatieven):
        if toevoeging in mapping:
            alternatieven.extend(mapping[toevoeging])

    # Empty toevoeging should always be an option
    alternatieven.append("")
    # Begane grond as last resort
    alternatieven.extend(begane_grond)
    # Return unique ordered items list
    return list(OrderedDict.fromkeys(alternatieven))


def create_improve_locations_tasks(all_invalid_locations):
    """
    For all items found in qs. Improve the location
    and start tasks by specifying search tasks that will
    likely match with ONE !! specific adres
    """

    log.debug('Finding incomplete adresses...')

    for loc in all_invalid_locations.iterator():

        addr = loc.volledig_adres

        # figure out with adresses / streetnames
        # could be alternative
        for alternative_addr in alternative_qs(addr):
            create_search_for_addr(loc, alternative_addr)


def dubbele_nummer_check(nummer, toevoeging):
    """
    straat 345 - 347

    Hiervoor zouden we naar 2! locaties moeten zoeken
    """

    # neven adres?
    if toevoeging and toevoeging.isdigit():
        if abs(int(nummer) - int(toevoeging)) < 3:
            nummer2 = toevoeging
            return nummer2


def determine_postcode_index(tokens, postcode):
    """
    postcode is in the tokens.
    """
    #log.debug(tokens)
    #log.debug(postcode)

    if not postcode:
        return len(tokens)

    number = postcode[:4]

    for idx, t in enumerate(tokens):
        if t == number:
            return idx


def create_search_for_addr(loc, addr):
    """
    Create search tasks for specific adres
    """
    query_string, tokens = clean_tokenize(addr)
    i = is_straat_huisnummer(tokens)

    toevoeging = None

    postcode = re.search("\d\d\d\d[A-Z][A-Z]", addr)

    if postcode:
        postcode = postcode.group()
    else:
        log.error(addr)

    straat = " ".join(tokens[:i])
    nummer = tokens[i]

    toevoegingen = []  # List with possible options

    if not straat:
        loc.correctie = False
        loc.save()
        log.error(addr)
        return

    if len(tokens) > i:
        idx = determine_postcode_index(tokens, postcode)
        toevoegingen = tokens[i+1:idx]
        #log.debug('toevoegingen: %s', toevoegingen)
        # FIX common toevoeging mistakes
        toevoegingen = normalize_toevoeging(toevoegingen)
        #log.debug('toevoegingen2: %s', toevoegingen)

    # add search tasks to queue
    while SEARCHES_QUEUE.full():
        gevent.sleep(2.3)

    huisnummers = [nummer]

    nummer2 = dubbele_nummer_check(nummer, toevoeging)

    if nummer2:
        huisnummers.append(nummer2)
        toevoegingen = toevoegingen or BEGANE_GROND

    search_data = [loc, query_string,
                   straat, huisnummers, toevoegingen, postcode]

    SEARCHES_QUEUE.put(search_data)


def create_qs_of_invalid_locations(gemeente):
    """
    Create a qs of invalid locations.

    - Invalid are locations with no geomatrie,
    - Having an adres withing 'gemeente'
    - No correction has been attempted
    """

    return Locatie.objects \
        .filter(geometrie__isnull=True) \
        .filter(bag_vbid__isnull=True) \
        .filter(volledig_adres__endswith=gemeente) \
        .exclude(volledig_adres__startswith='Postbus') \
        .filter(correctie__isnull=True)


def guess():
    """
    Do an search on street housenumber part of volledig adres and try to
    find geo_point
    """
    log.debug('Start Finding and correcting incomplete adresses...')
    status_job = gevent.spawn(req_counter)

    for gemeente in GEMEENTEN:
        invalid_locations = create_qs_of_invalid_locations(gemeente)

        count = invalid_locations.count()

        if count == 0:
            continue

        STATS['total'] = count + 1  # prevent devide by zero errors

        STATS['onbekend'] = 0
        log.debug('\n Processing gemeente {} {} \n'.format(gemeente, count))

        jobs = [gevent.spawn(
            create_improve_locations_tasks, invalid_locations)]

        for _ in range(WORKERS):
            jobs.append(
                gevent.spawn(async_determine_rd_coordinates))

        with gevent.Timeout(3600, False):
            # waint untill all search tasks are done
            # but no longer than an hour
            gevent.joinall(jobs)

        # store corrections for each gemeente
        STATS[gemeente] = STATS['correcties']

        log.debug('\nCorrecties %s Duration %i seconds\n',
                  STATS['correcties'], time.time() - STATS['start'])

        # reset correcties count
        STATS['correcties'] = 0

    status_job.kill()
    # log end result
    for gemeente in GEMEENTEN:
        if gemeente not in STATS:
            continue
        log.debug('%s - correcties: %s', gemeente, STATS[gemeente])

    total_seconds = time.time() - STATS['start']
    log.debug('\nTotal Duration %i m: %i\n',
              total_seconds / 60.0, total_seconds % 60)
