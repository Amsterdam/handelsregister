"""
Slurp alle categorien en subcategorien van de cbs website af om met deze code's
de goede geo data tabel te kunnen maken.
"""

import requests
import time


all_category_codes = {}

code = 'start/0'
vraag_url = 'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/sbianswer/getNextQuestion/{}'

# find actual sbi codes
search_url = 'http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBISearch/search/{}'

start_codes = {}

data = requests.get(vraag_url.format(code))
json_data = data.json()


for antwoord in data.json()['Answers']:
    antwoord_code = antwoord['Value']
    hoofd_category = antwoord['Key']
    all_category_codes[hoofd_category] = {}

    next_url = vraag_url.format(antwoord_code)
    next_url += '/1'

    # detail handel
    print(hoofd_category)
    # print(next_url)

    #
    category_data = requests.get(next_url)

    # subantwoorden = category_data.json()['Answers']
    for sub_category_antwoord in category_data.json()['Answers']:

        sub_category_sbi_codes = []
        sub_cat = sub_category_antwoord['Key']

        print(sub_cat)
        all_category_codes[hoofd_category][sub_cat] = []

        category_url_code = sub_category_antwoord['Value']

        search_url_k = search_url.format(category_url_code)

        # print(search_url_k)
        category_codes = requests.get(search_url_k)

        time.sleep(0.1)

        for item in category_codes.json():
            # print(category_codes.json())
            if not item:
                continue
            all_category_codes[hoofd_category][sub_cat].append(item['Code'])

    print(all_category_codes[hoofd_category][sub_cat])

for category, sub_cats in all_category_codes.items():
    print(category)
    for sub_cat, codes in sub_cats.items():
        print(u'      {}'.format(sub_cat))
        print(u'          {}'.format(codes))

#print(data.json())
