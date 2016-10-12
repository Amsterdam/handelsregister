"""

- Vind via het volledig_adres veld alle vestigingen in een gemeente.
- Bouw per gemeente een sql copy statement dat alle locaties geeft
  zonder geo informatie.
- execute sql like so on the local docker:
    - psql -h 127.0.0.1 -p 5406 -U handelsregister handelsregister --file create_csv_sbi.sql
- enjoy the csv data!

"""

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


copy_sql_with_sbi = \
    "\Copy ({}) TO 'hr_ves_{}_sbi.csv' WITH DELIMITER ',' CSV HEADER\n"

copy_sql = "\Copy ({}) TO 'hr_ves_{}.csv' WITH DELIMITER ',' CSV HEADER\n"

select_sql_sbi = """
SELECT
    vestiging_id,
    vestigingsnummer,
    hoofdvestiging,
    volledig_adres,
    datum_aanvang,
    datum_einde,
    naam,
    sbi_code,
    hoofdactiviteit,
    toevoeging_adres,
    postbus_nummer,
    bag_numid,
    bag_vbid,
    straat_huisnummer,
    postcode_woonplaats,
    regio,
    land,
    geometrie
    FROM hr_vestiging_activiteiten hr_a
        JOIN hr_vestiging vs
        ON hr_a.vestiging_id = vs.id
        JOIN hr_activiteit a
        ON a.id = hr_a.activiteit_id
        JOIN hr_locatie loc
        ON (vs.bezoekadres_id = loc.id
            OR vs.postadres_id = loc.id)
            AND ST_IsValid(loc.geometrie) is null

        WHERE volledig_adres LIKE '%{}%'
        ORDER BY volledig_adres
"""

select_sql = """
SELECT
    vestigingsnummer,
    hoofdvestiging,
    volledig_adres,
    datum_aanvang,
    datum_einde,
    naam,
    toevoeging_adres,
    postbus_nummer,
    bag_numid,
    bag_vbid,
    straat_huisnummer,
    postcode_woonplaats,
    regio,
    land,
    geometrie
    FROM hr_vestiging vs
        JOIN hr_locatie loc
        ON (vs.bezoekadres_id = loc.id
            OR vs.postadres_id = loc.id)
            AND ST_IsValid(loc.geometrie) is null
        WHERE volledig_adres LIKE '%{}%'
        ORDER BY volledig_adres
"""

# create csv with sbi codes
WITH_SBI = False


if WITH_SBI:
    the_select = select_sql_sbi
    sql_file_name = 'create_csv_ves_sbi.sql'
else:
    sql_file_name = 'create_csv_ves.sql'
    the_select = select_sql


with open(sql_file_name, 'w') as target_file:

    copy_lines = []

    for city in gemeenten:
        # create the select query for a specific city
        city_select = the_select.format(city)
        # join the statement one one single line this
        # is a psql meta command requirement
        one_line = " ".join(city_select.splitlines())
        # make a copy statement
        statement = copy_sql.format(one_line, city)
        # add line to results
        copy_lines.append('\echo {}'.format(city))
        copy_lines.append(statement)

    # write sql all lines to file
    target_file.write("".join(copy_lines))
    print("""
      SQL File generated: {}  Run this agains your docker database:
      to get a csv with all vestigingen with missing geometry data.

      psql -h 127.0.0.1 -p 5406 -U handelsregister handelsregister --file {}
    """.format(sql_file_name, sql_file_name))
