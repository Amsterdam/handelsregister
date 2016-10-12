
from .models import Locatie

import re
import string
import requests


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


def improve_locations(qs):

    for loc in qs[:100]:
        addr = loc.volledig_adres

        if addr.startswith('Postbus'):
            continue

        print(addr)

        query_string, tokens = clean_tokenize(addr)
        i = is_straat_huisnummer(query_string, tokens)

        print('{} {}'.format(" ".join(tokens[:i]), tokens[i]))

        continue

        parameters = {
            'q': '{} {}'.format()
        }

        requests.get(search_adres_url, parameters)


def guess():
    for gemeente in gemeenten:
        qs = Locatie.objects\
            .filter(geometrie__isnull=True) \
            .filter(volledig_adres__contains='Amsterdam')

        count = qs.count()
        print('\n Processing gemeente {} \n'.format(count))

        improve_locations(qs)
        break
