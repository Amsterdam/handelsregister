"""
With the datapunt search api we can greatly improve
location quality of the datasets

./manage.py run_import --testsearch

"""

# NOTE BELOW MUST BE done in manage_gevent.py!!
# from gevent import monkey
# monkey.patch_all(thread=False, select=False)

import datetime
import os
import re
import json
import string
import logging
import time
import editdistance

from collections import OrderedDict

from requests import Session
import grequests

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q

import gevent
from gevent.queue import JoinableQueue

from .models import Locatie

log = logging.getLogger(__name__)

SEARCHES_QUEUE = JoinableQueue(maxsize=1500)

# TO see step by step what search does.
SLOW = False

STATS = dict(
    start=time.time(),
    correcties=0,
    onbekend=0,
    total=50,  # prevent by zero errors
    fixs=0,
    left=0,
)

STRAATLEVEL = 0
POSTCODELEVEL = 200
P6LEVEL = 1000

# the amount of concurrent workers that do requests
# to the search api
WORKERS = 10

if SLOW:
    WORKERS = 1  # 25

# By default we search against ACC to not pollute graphs in kibana
SEARCH_URL_BASE = os.getenv("SEARCH_URL_BASE", "https://api.data.amsterdam.nl")
SEARCH_ADRES_URL = '{}/atlas/search/adres/'.format(SEARCH_URL_BASE)
# ?huisnummer=105&postcode=1018WR"
PCODE_URL = "{}/bag/v1.1/nummeraanduiding/".format(SEARCH_URL_BASE)


# These urls are used to be SAVED at the locaton object
ROOT = "https://api.datA.amsterdam.nl"
NUM_URL = "{}/bag/v1.1/nummeraanduiding".format(ROOT)
VBO_URL = "{}/bag/v1.1/verblijfsobject".format(ROOT)


def make_status_line():
    status_line = 'All %s fixed: %s  ?: %s  fix/s %s  left: %s \r'
    complete_status_line = status_line % (
        STATS['total'],
        STATS['correcties'],
        STATS['onbekend'],
        STATS['fixs'],
        STATS['left']
    )
    return complete_status_line


def fix_counter():
    """
    Get an indication of the request per second
    """
    interval = 3.0

    while True:
        start = STATS['correcties']
        gevent.sleep(interval)
        diff = STATS['correcties'] - start + 0.001
        speed = (diff // interval) + 1
        STATS['fixs'] = '%.2f' % speed
        seconds_left = abs((STATS['total'] + 1) - STATS['correcties']) // speed
        STATS['left'] = datetime.timedelta(seconds=seconds_left)
        log.info(make_status_line())


class LOGHANDLER():
    """
    set up some logging
    """
    wtf = logging.getLogger('onbekend')
    bag_error = logging.getLogger('bagerror')

    def __init__(self):
        if not settings.DEBUG:
            self.wtf.setLevel(logging.CRITICAL)
            self.bag_error.setLevel(logging.CRITICAL)


LOG = LOGHANDLER()


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

    remove = [
     " tegenover",
     " t o",
    ]

    try_first = []

    def woonbootfix(qs):
        # woonboot fix
        if qs.endswith('ab'):
            qs_new = qs.replace(' ab', "")
            try_first.append(qs_new)

    for unwanted in remove:
        if unwanted in query_string:
            qs_new = query_string.replace(unwanted, "")
            try_first.append(qs_new)

    for patern, replace in could_also_be:
        if query_string.startswith(patern):
            qs_new = query_string.replace(patern, replace)
            alternatives.append(qs_new)

    woonbootfix(query_string)

    try_first.extend(alternatives)
    return try_first


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


def is_straat_huisnummer(tokens) -> int:
    """
    Check if unpunt contains a steer and number, return token index.

    0 nothing found.
    i > 0  = index token
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

    def get_response(self, parameters={}, url=SEARCH_ADRES_URL):
        """
        Actualy do the http api search call
        """
        # parameters = {'q': self.get_q()}
        async_r = grequests.get(url, params=parameters, session=self.session)
        # send a request and wait for results
        gevent.spawn(async_r.send).join()
        # Do something with the result count?

        if async_r.response is None:
            log.error('RESPONSE NONE %s %s', url, parameters)
            return {}

        if async_r.response.status_code == 404:
            log.error('404 %s %s', url, parameters)
            return {}

        if not async_r.response:
            log.error('NO RESPONSE %s %s', url, parameters)
            return {}

        result_json = async_r.response.json()

        return result_json

    def determine_rd_coordinates(self):
        """
        Send adres requests to atlas to determine geo point and
        landelijk bag id of items

        If there is more then one hit try get more exact match
        with a search complete with 'toevoegingen'
        """

        # find nummeraanduiding hit that comes close to what we look for
        correctie_level, num = self.get_search_response()

        if not num:
            # nothing found return
            # is already logged.
            return

        rds_bagid = []
        point, bag_id, num_id = self.get_details_for_vbo(num)

        if point:
            rds_bagid.append((point, bag_id))
            # The first point is enough

        if rds_bagid:
            self.save_corrected_geo_infomation(
                num, point, bag_id, num_id, correctie_level)
        else:
            log.exception('Point/Bagid missing: %s', num)
            self.log_wtf_loc()
            return

    def get_q(self, toevoeging, nummer=None, postcode=None):
        """
        Create query string for search
        """
        if not nummer:
            nummer = self.nummers[0]

        if postcode:
            return '{} {} {}'.format(postcode, nummer, toevoeging)

        return '{} {} {}'.format(
            self.straatnaam, nummer, toevoeging)

    def get_hits(self, qs_try, nummer):

        # straat/postcode huisnummer toevoeging
        parameters_toevoeging = {'q': qs_try}

        data = self.get_response(parameters_toevoeging)

        # Only if we are realy sure we return data

        if SLOW:
            count = 0
            if data:
                count = data.get('count', 0)
            log.debug('q=%s hits=%s', qs_try, count)

        valid_hits = []

        if data and data.get('results') and data['count'] > 0:
            for hit in data.get('results'):
                if hit['huisnummer'] == nummer:
                    valid_hits.append(hit)

        # self.used_query_string = qs_try

        return valid_hits

    def match_hit(self, nummer, toevoeging_optie, hits, exact=True):
        """
        go look for a match. exact or startswith
        """
        for hit in hits:

            suggestion = '{} {}'.format(nummer, toevoeging_optie).lower()
            # stip exessive white space
            suggestion = suggestion.strip()

            hit_toevoeging = hit['toevoeging'].lower()

            if exact:
                if str(hit_toevoeging) == str(suggestion):
                    return hit
            else:
                if hit_toevoeging.startswith(suggestion):
                    return hit

    def filter_hits(self, hits):
        """
        Solves nasty edge case.

        'Nes 33 1012KC Amsterdam' -> 'Nes 33-H'

        NOT Aert van Nesstraat 33

        """
        new_hits = []

        for hit in hits:
            hit_straat = hit['straatnaam'].lower()
            distance = editdistance.eval(hit_straat, self.straatnaam)

            if not distance:
                # we have an ~exactisch street name match.
                # trumps other matches.
                new_hits.append(hit)

        # no exact matching streetname..
        if not new_hits:
            return hits

        return new_hits

    def look_in_hits(self, hits, nummer):
        """
        Look in hits for matching hit to see if there is a
        hit with a correct / matching toevoeging

        # TODO mach streetnames!
        # OR make relevancy search endpoint available..

        H hit is better then.
        """
        # filter hits by streetname
        # see test example with hit NES 33.
        hits = self.filter_hits(hits)

        # Try to find hit in hits that exactly matches toevoegingen
        for tindex, tv_optie in enumerate(self.toevoegingen):
            # find exact hits
            hit = self.match_hit(nummer, tv_optie, hits)
            if hit:
                return tindex, hit

        # Try to find hit in hits that startswith toevoegingen
        for tindex, tv_optie in enumerate(self.toevoegingen):
            # find exact hits
            hit = self.match_hit(nummer, tv_optie, hits, exact=False)
            if hit:
                return tindex + 5, hit

        return None, None

    def find_postcode_hit(self):
        """
        All numbers have failed. Try to find hit with postcode
        """
        # last restort try poscode and take first hit

        log.debug('P6 %s' % self.postcode)

        if self.postcode:
            data = self.get_response(
                {'postcode': self.postcode.upper()}, url=PCODE_URL)

            hits = data.get('results')

            if data and hits and data['count'] > 0:
                # just return first result
                log.debug('P6 HIT')
                return hits[0]

    def get_search_response(self):
        """
        Given straatnaam, nummer and toevoeging try to
        find search result as last resort try postcode

        return correctie_level, hit
        """
        hits = None

        # First with toevoeging
        for i, nummer in enumerate(self.nummers):

            correctie_level = i*10 + STRAATLEVEL

            # get all hits with straat huisnummer
            qs_try = self.get_q("", nummer=nummer)
            hits = self.get_hits(qs_try, nummer)

            if not hits:
                # get all hits with postcode huisnummer
                qs_try = self.get_q("", nummer=nummer, postcode=self.postcode)
                hits = self.get_hits(qs_try, nummer)
                if hits:
                    correctie_level += POSTCODELEVEL

            if SLOW:
                gevent.sleep(0.5)

            # IF hits then check toevoegingen.
            if hits:
                ti, match = self.look_in_hits(hits, nummer)
                # add toevoeging level
                if match:
                    # the closer the toevoeging the better score.
                    correctie_level += ti
                    return correctie_level, match
                # no toevoeging match given.
                return correctie_level, hits[0]

            # for debugging
            if SLOW:
                gevent.sleep(0.5)

        # As a last resort find something with the P6 postcode
        hit = self.find_postcode_hit()

        if hit:
            correctie_level += P6LEVEL  # postcode_hit
            return correctie_level, hit

        # Correctie failed
        # save and log empty result result

        self.locatie.refresh_from_db()

        if self.locatie.correctie is None:
            self.locatie.correctie = False
            self.locatie.save()
            self.log_wtf_loc()

        return 9999, []

    def log_wtf_loc(self):
        """
        nothing found
        """
        LOG.wtf.debug(
            '%s, %s, %s, %s, %s, %s',
            self.locatie.id,
            self.straatnaam,
            self.postcode,
            self.nummers,
            self.toevoegingen,
            self.query_string)

        STATS['onbekend'] += 1

    def _get_vbo_url(self, details):

        vbo_url = None
        # a nummeraanduiding result needs more vbo data
        # van een nummeraanduiding vind het vbo object
        if details.get('verblijfsobject'):
            vbo_url = details['verblijfsobject']
        elif details.get('ligplaats'):
            vbo_url = details['ligplaats']
        elif details.get('standplaats'):
            vbo_url = details['standplaats']

        return vbo_url

    def _get_num_id(self, details):
        num_id = None

        street_number = f"{self.straatnaam} {self.nummers[0]}" if self.straatnaam and self.nummers else None
        if details.get('hoofdadres'):
            # Check if hoofdadres is the adress we search for, otherwise try to use one of the other adresses
            if details['hoofdadres']['_display'][:len(street_number)].lower() == street_number or not street_number:
                num_id = details['hoofdadres'].get("landelijk_id")
        if not num_id and details.get('adressen'):
            num_url = details['adressen']['href']
            num_details = self.get_response(url=num_url)
            results = num_details.get('results', [])
            for result in results:
                if result['_display'][:len(street_number)].lower() == street_number:
                    num_id =  result.get('landelijk_id')
                    break
            if not num_id and results:
                num_id = results[0].get('landelijk_id')

        return num_id

    def get_details_for_vbo(self, num):
        """
        Get the detail of a specific verblijsobject/ligplaats/standplaats
        """

        details_url = num['_links']['self']['href']

        # search result has all data
        # but could also be nummeraanduidng endpoint
        details = self.get_response(url=details_url)

        vbo_url = self._get_vbo_url(details)

        if vbo_url:
            details = self.get_response(url=vbo_url)

        if 'geometrie' in details:
            if not details.get('geometrie'):
                log.exception('invalid details')
            else:
                point = details['geometrie']
        else:
            point = self.locatie.geometrie

        num_id = self._get_num_id(details)

        # determine bag_id
        for key in [
                'verblijfsobjectidentificatie',
                'ligplaatsidentificatie',
                'standplaatsidentificatie',
                ]:

            bag_id = details.get(key)

            if bag_id:
                break

        if not bag_id:
            raise ValueError('bag_id missing')

        return point, bag_id, num_id

    def save_corrected_geo_infomation(
            self, num, point, bag_id, num_id, correctie_level):
        """
        New additional location data is found, save it
        """
        try:
            geometrie = normalize_geo(point)
        except TypeError:
            log.error('POINT ERROR %s', point)
            return

        assert geometrie
        assert bag_id

        # we found a probably correct bag_id.
        # this is not 100% sure.
        self.locatie.bag_vbid = bag_id

        if num_id:
            self.locatie.bag_numid = num_id

        self.locatie.bag_nummeraanduiding = "{}/{}/".format(NUM_URL, num_id)
        self.locatie.bag_adresseerbaar_object = \
            "{}/{}/".format(VBO_URL, bag_id)

        self.bag_id = bag_id

        locatie = self.locatie
        # we succesfull did a correction
        locatie.correctie = True
        locatie.correctie_level = correctie_level
        locatie.query_string = num['_display']
        locatie.geometrie = geometrie

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
        try:
            task.determine_rd_coordinates()
        except Exception:
            # when tasks fails.. continue..
            log.error('\n\n\n')
            log.exception('Oops')
            log.error('\n\n\n')


def normalize_geo(point):
    """
    If we encounter a polygon. change it to point
    """

    if point['type'] == 'Point':
        n_point = GEOSGeometry(json.dumps(point))
    elif point['type'] == 'Polygon':
        # create centroid from polygon (ligplaats)
        n_point = GEOSGeometry(json.dumps(point)).centroid

    # geojson now defaults to 4326!
    n_point.srid = 28992
    return n_point


def normalize_toevoeging(toevoegingen=[""]):
    """
    zoek toevoeging indicaties
    en alle alternatieven
    """

    toevoegingen = [t.lower() for t in toevoegingen]

    alternatieven = [
        "".join(toevoegingen),
        " ".join(toevoegingen),
    ]

    # generate from specific to less specific alternatives for
    # toevoegingen
    for i in reversed(range(len(toevoegingen))):
        optie = " ".join(toevoegingen[:i])
        if optie:
            alternatieven.append(optie)

    begane_grond = ['H', 1, 'A', 'O']

    mapping = {
        '1hg': [1, 2],
        '2hg': [2, 3],
        '3hg': [3, 4],
        'iii': [3, 4],
        'ii': [2, 3],
        'i': ['1', 'H', 'A', 'O'],
        'a': begane_grond,
        'b': [1, 2],
        'c': [2, 3],
        'd': [3, 2, 4],
        'e': [4, 3, 2],
        'bg': begane_grond,
        'huis': begane_grond,
        'h': begane_grond,
        'hs': begane_grond,
        'sous': begane_grond,
        'bel': begane_grond,
        'parterre': begane_grond,
        'part': begane_grond
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

        addr = loc.volledig_adres.lower()

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

    if not postcode:
        return len(tokens)

    number = postcode[:4]

    for idx, t in enumerate(tokens):
        if t == number:
            return idx


def current_toevoegingen(huisnummer_i, tokens, postcode):

    if len(tokens) < huisnummer_i:
        return []

    idx = determine_postcode_index(tokens, postcode)
    toevoegingen = tokens[huisnummer_i+1:idx]
    return toevoegingen


def determine_toevoegingen(hi, tokens, postcode):
    """
    Determine specific toevoegingen which apply
    """

    toevoegingen = []  # List with possible options
    toevoegingen = current_toevoegingen(hi, tokens, postcode)
    # FIX common toevoeging mistakes

    tv = []
    for token in toevoegingen:
        for char in token:
            tv.append(char)

    toevoegingen = normalize_toevoeging(tv)

    return toevoegingen


def determine_relevant_huisnummers(hi, nummer, tokens, postcode):
    """
    Given nummer and toevoeging determine relevant nummers
    sometimes bakkertje - utrechtste straat 30-32
    mean we should search for 30 AND 32

    input = 30-32

    output = [30, 32, 28, 34, 36]

    remove 32 from toevoegingen / tokens
    """

    toevoegingen = current_toevoegingen(hi, tokens, postcode)

    huisnummers = [nummer]

    if toevoegingen:
        toevoeging = toevoegingen[0]

        nummer2 = dubbele_nummer_check(nummer, toevoeging)

        if nummer2:
            huisnummers.append(int(nummer2))
            tokens.remove(nummer2)

    less = range(nummer-2, nummer-8, -2)
    more = range(nummer+2, nummer+8, 2)

    numbers_by_distance = [j for i in zip(less, more) for j in i]

    huisnummers.extend(numbers_by_distance)

    return huisnummers


def create_search_for_addr(loc, addr):
    """
    Create search tasks for specific adres
    """
    query_string, tokens = clean_tokenize(addr)

    huisnummer_i = is_straat_huisnummer(tokens)

    # toevoeging = None

    postcode = re.search("\d\d\d\d[a-z][a-z]", addr)

    if postcode:
        postcode = postcode.group()
    else:
        log.error('No postcode %s' % addr)

    straat = " ".join(tokens[:huisnummer_i])
    nummer = int(tokens[huisnummer_i])

    if not straat:
        loc.correctie = False
        log.error(addr)
        return

    huisnummers = determine_relevant_huisnummers(
            huisnummer_i, nummer, tokens, postcode)

    toevoegingen = determine_toevoegingen(
            huisnummer_i, tokens, postcode)

    # add search tasks to queue
    while SEARCHES_QUEUE.full():
        gevent.sleep(2.3)

    # generate the most relevant huisnummer for this adres
    # also take in account the most relevant neighbours

    search_data = [
       loc, query_string,
       straat, huisnummers, toevoegingen, postcode]

    SEARCHES_QUEUE.put(search_data)

    return search_data


def create_qs_of_invalid_locations(gemeente):
    """
    Create a qs of invalid locations.

    - Invalid are locations with no geometrie,
    - Having an adres withing 'gemeente'
    - No correction has been attempted
    """

    return (
        Locatie.objects
        .filter(Q(geometrie__isnull=True) | Q(bag_vbid__isnull=True))
        .filter(volledig_adres__endswith=gemeente)
        .exclude(volledig_adres__startswith='Postbus')
        .filter(correctie__isnull=True)
        #
        # keep commented code as reference for now
        # .extra(
        #    tables=['hr_vestiging'],
        #    where=[
        #        '"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"',
        #    ])
    )


def wait_for_filled_queue():

    with gevent.Timeout(5, False):
        # give worker some time
        # to add search cases
        while True:
            if SEARCHES_QUEUE.empty():
                gevent.sleep(1.5)
            else:
                break


def run_workers(jobs):
    """
    Run X workers processing search tasks
    """

    for _ in range(WORKERS):
        jobs.append(
            gevent.spawn(async_determine_rd_coordinates)
        )

    with gevent.Timeout(3600, False):
        # waint untill all search tasks are done
        # but no longer than an hour
        gevent.joinall(jobs)


def guess():
    """
    Do an search on street housenumber part
    of full adress and try to find geo_point (rd)
    """
    log.debug('Start Finding and correcting incomplete adresses...')

    status_job = gevent.spawn(fix_counter)

    for gemeente in GEMEENTEN:

        invalid_locations = create_qs_of_invalid_locations(gemeente)

        if SLOW:
            invalid_locations = invalid_locations[:10]

        count = invalid_locations.count()

        # no invalid locations for gemeente..
        if count == 0:
            continue

        STATS['total'] = count + 1  # prevent devide by zero errors

        STATS['onbekend'] = 0

        log.debug('\n Processing gemeente {} {} \n'.format(gemeente, count))

        #
        jobs = [gevent.spawn(
            create_improve_locations_tasks, invalid_locations)]

        wait_for_filled_queue()

        run_workers(jobs)
        # store corrections for each gemeente
        STATS[gemeente] = STATS['correcties']

        log.debug('\nCorrecties %s Duration %i seconds\n',
                  STATS['correcties'], time.time() - STATS['start'])

        # reset correcties count
        STATS['correcties'] = 0

        # check if we did a good job doing corrections.
        # normally about ~60 invalid locations left of 10.000
        num_invalid_locations = invalid_locations.count()
        assert num_invalid_locations < 1000, \
            "Out of {initial_invalid_locations} initial invalid locations, {num_invalid_locations} still exist"\
                .format(initial_invalid_locations=count, num_invalid_locations=num_invalid_locations)

    status_job.kill()

    # log end result
    for gemeente in GEMEENTEN:
        if gemeente not in STATS:
            continue
        log.debug('%s - correcties: %s', gemeente, STATS[gemeente])

    # check if we did any corrections.
    assert STATS['Amsterdam'] > 0

    total_seconds = time.time() - STATS['start']
    log.debug('\nTotal Duration %i m: %i\n',
              total_seconds / 60.0, total_seconds % 60)


def test_one_weird_one(test="", target=""):
    """
    Method to check manualy what this search does for 1 item.
    to use in the shell_plus
    """

    test_this = 'Nieuwe Looiersstraat 45d 1017VB Amsterdam'

    if test:
        test_this = test

    query_string, tokens = clean_tokenize(test_this)
    loc = Locatie.objects.first()
    loc.volledig_adres = test_this

    global SLOW
    SLOW = True

    options = alternative_qs(query_string)

    for alternative_addr in options:
        create_search_for_addr(loc, alternative_addr)

    # fix it
    async_determine_rd_coordinates()

    test_ok = loc.query_string == target

    loc.refresh_from_db()

    result = f"""

    test:        {test_this}
    bag_id:      {loc.bag_vbid}
    correctie    {loc.correctie}
    geometrie:   {loc.geometrie}
    result:      {loc.query_string}
    should:      {target}

    {test_ok}

    """
    log.debug(result)

    return test_ok


buggy_voorbeelden = [
    ('Haarlemmerweg 8 1014BE Amsterdam', 'Haarlemmerweg 8A'),

    ('Pieter Pauwstraat 18 hs 1017ZK Amsterdam', 'Pieter Pauwstraat 18-H'),
    ('Haarlemmermeerstraat 99 huis 1058JT Amsterdam',
        'Haarlemmermeerstraat 99-H'),
    ('Frederik Hendrikstraat 128 part  1052JC Amsterdam',
        'Frederik Hendrikstraat 128-H'),
    ('Lindengracht 254 BG 1015KN Amsterdam', 'Lindengracht 254-H'),
    ('Jacob Obrechtstraat 39 -hs 1071KG Amsterdam',
        'Jacob Obrechtstraat 39-H'),

    ('Silodam 340 1013AW Amsterdam', 'Silodam 340'),
    ('Keizersgracht 62 -64 1015CS Amsterdam', 'Keizersgracht 62'),

    ('tt. Neveritaweg 33 1033WB Amsterdam', 'tt. Neveritaweg 27'),
    ('Haarlemmerstraat 24 - 26 1013ER Amsterdam', 'Haarlemmerstraat 24-H'),
    ('Hoogte Kadijk 143 F26 1018BH Amsterdam', 'Hoogte Kadijk 143F-26'),

    ('Geleenstraat 46 I 1078LG Amsterdam', 'Geleenstraat 46-1',),
    ('Ruysdaelstraat 49 B 7 1071XA Amsterdam', 'Ruysdaelstraat 49B-7'),
    ('Nieuwe Ridderstraat 4 - 6 1011CP Amsterdam', 'Nieuwe Ridderstraat 6'),
    ('Raadhuisstraat 22 1016DE Amsterdam', 'Raadhuisstraat 20'),  # even nummer
    ('Vossiusstraat 52 1071AK Amsterdam', 'Vossiusstraat 50-H'),

    ('Nes 33 1012KC Amsterdam', 'Nes 33-H'),
    ('Oudezijds Voorburgwal 300 1012GL Amsterdam', 'Oudezijds Voorburgwal 300'),

    # WONTFIX
    ('Oude Schans t/o 14 1011LK Amsterdam', '?'),

]


def test_bad_examples():
    if Locatie.objects.count() == 0:
        Locatie.objects.create(afgescherm=True)

    ok = 0
    fail = 0

    for example, target in buggy_voorbeelden:
        if test_one_weird_one(test=example, target=target):
            ok += 1
        else:
            fail += 1

    log.debug(f'OK: {ok}  FAIL: {fail}')
