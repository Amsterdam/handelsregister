# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from geo_views import migrate

from django.conf import settings


from django.contrib.sites.models import Site


def create_site(apps, *args, **kwargs):
    Site.objects.create(
        domain=settings.DATAPUNT_API_URL,
        name='API Domain'
    )


def delete_site(apps, *args, **kwargs):
    Site.objects.filter(name='API Domain').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '__first__'),
        ('hr', '__first__'),
    ]

    operations = [
        # set the site name
        migrations.RunPython(code=create_site, reverse_code=delete_site),
        # create the hr views
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties",
            sql="""
SELECT
  ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('4120', '42111', '42112', '4212', '4213', '4221', '4222', '4291',
      '4299', '4311', '4312', '4313', '4321', '43221', '43222', '4329', '4331', '4332',
      '4333', '4334', '4339', '4391', '43991', '43992', '43993', '43999') THEN 'bouw overig'
    WHEN a.sbi_code in ('4321', '43221', '43222', '4329') THEN 'bouwinstallatie'
    WHEN a.sbi_code in ('4331', '4332', '4333', '4334', '4339') THEN 'afwerking van gebouwen'
    WHEN a.sbi_code in ('4391', '43991', '43992', '43993', '43999') THEN 'dak- en overige gespecialiseerde bouw'
    WHEN a.sbi_code in ('42111', '42112', '4212', '4213', '4221', '4222', '4291', '4299') THEN 'grond, water, wegenbouw'
    WHEN a.sbi_code = '4120' THEN 'bouw/utiliteitsbouw algemeen / klusbedrijf'
    WHEN a.sbi_code in ('85201', '85202', '85203', '85311', '85312', '85313', '85314', '85321', '85322', '85323', '8541',
      '8542', '85511', '85519', '85521', '85522', '8553', '85591', '85592', '85599', '8560') THEN 'onderwijs'
    WHEN a.sbi_code in ('86101', '86102', '86103', '86104', '8621', '86221', '86222', '86231', '86232', '86911',
      '86912', '86913', '86919', '86921', '86922', '86923', '86924', '86925', '86929', '8710', '8720', '87301',
      '87302', '87901', '87902', '88101', '88102', '88103', '88911', '88912', '88991', '88992', '88993', '88999')
        THEN 'gezondheids- en welzijnszorg'
    WHEN a.sbi_code in ('8411', '8412', '8413', '8421', '8422', '84231', '84232', '8424', '8425', '8430') THEN 'overheid'
    WHEN a.sbi_code in ('3321', '33221', '33222', '33223', '3323', '3324', '3329') THEN 'installatie (geen bouw)'
    WHEN a.sbi_code in ('3311', '33121', '33122', '33123', '3313', '3314', '3315', '3316', '3317', '3319', '9511',
    '9512', '9521', '9522', '9523', '9524', '9525', '9529') THEN 'reparatie (geen bouw)'
    WHEN a.sbi_code in ('1011', '1012', '1013', '1020', '1031', '1032', '1039', '1041', '1042', '1051', '1052',
    '1061', '1062', '1071', '1072', '1073', '1081', '10821', '10822', '1083', '1084', '1085', '1086', '1089',
    '1091', '1092', '1101', '1102', '1103', '1104', '1105', '1106', '1107', '1200', '1310', '1320', '1330', '1391',
    '1392', '1393', '1394', '1395', '1396', '1399', '1411', '1412', '1413', '1414', '1419', '1420', '1431', '1439',
    '1511', '1512', '1520', '16101', '16102', '1621', '1622', '16231', '16239', '1624', '1629', '1711', '17121',
    '17122', '17129', '17211', '17212', '1722', '1723', '1724', '1729', '1811', '18121', '18122', '18123', '18124',
    '18125', '18129', '1813', '1814', '1820', '1910', '19201', '19202', '2011', '2012', '2013', '20141', '20149',
    '2015', '2016', '2017', '2020', '2030', '2041', '2042', '2051', '2052') THEN 'productie'
    WHEN a.sbi_code in ('7810', '78201', '78202', '78203', '7830') THEN 'arbeidsbemiddeling, uitzendbureaus, uitleenbureaus'
    WHEN a.sbi_code in ('74201', '74202', '74203', '7430', '7490', '8010', '8020', '8030', '8110', '8121',
    '81221', '81222', '81229', '8129', '8130', '8211', '8219', '8220', '8230', '8291', '8292', '82991',
    '82992', '82999') THEN 'overige zakelijke dienstverlening'
    WHEN a.sbi_code in ('7311', '7312', '7320') THEN 'reclame en marktonderzoek'
    WHEN a.sbi_code = '71112' THEN 'interieurarchitecten'
    WHEN a.sbi_code in ('70221', '70222') THEN 'managementadvies, economisch advies'
    WHEN a.sbi_code in ('7112', '71201', '71202', '71203', '72111', '72112', '72113', '72191',
    '72192', '72193', '72199', '7220') THEN 'technisch ontwerp, advies, keuring/research'
    WHEN a.sbi_code in ('74101', '74102', '74103') THEN 'design'
    WHEN a.sbi_code = '7021' THEN 'public relationsbureaus'
    WHEN a.sbi_code in ('69101', '69102', '69103', '69104', '69105') THEN 'advocaten rechtskundige diensten, notarissen'
    WHEN a.sbi_code = '71111' THEN 'architecten'
    WHEN a.sbi_code in ('69201', '69202', '69203', '69204', '69209') THEN 'accountancy, administratie'
    WHEN a.sbi_code in ('4910', '4920', '4931', '4932', '49391', '49392', '49393', '4941', '4942',
    '4950', '5010', '50201', '50202', '5030', '50401', '50402', '50403', '5110', '5121', '53202') THEN 'vervoer'
    WHEN a.sbi_code in ('4711', '47191', '47192', '4721', '47221', '47222', '4723', '47241',
    '47242', '4725', '4726', '47291', '47292', '47293', '47299', '4730', '4741', '4742', '47431',
    '47432', '47511', '47512', '47513', '47521', '47522', '47523', '47524', '47525', '47526',
    '47527', '47528', '4753', '47541', '47542', '47543', '47544', '47591', '47592', '47593',
    '47594', '47595', '47596', '47597', '4761', '4762', '4763', '47641', '47642', '47643', '47644',
    '4765', '47711', '47712', '47713', '47714', '47715', '47716', '47717', '47718', '47721', '47722',
    '4773', '47741', '47742', '4775', '47761', '47762', '47763', '4777', '47781', '47782', '47783',
    '47789', '47791', '47792', '47793', '47811', '47819', '4782', '47891', '47892', '47899', '47911',
    '47912', '47913', '47914', '47915', '47916', '47918', '47919', '47991', '47992', '47999')
      THEN 'detailhandel (verkoop aan consumenten, niet zelf vervaardigd)'
    WHEN a.sbi_code in ('4611', '4612', '4613', '4614', '4615', '4616', '4617', '4618', '4619')
      THEN 'handelsbemiddeling (tussenpersoon, verkoopt niet zelf)'
    WHEN a.sbi_code in ('52101', '52102', '52109') THEN 'opslag'
    WHEN a.sbi_code in ('5221', '5222', '5223', '52241', '52242', '52291', '52292') THEN 'dienstverlening vervoer'
    WHEN a.sbi_code in ('45111', '45112', '45191', '45192', '45193', '45194', '45201', '45202', '45203',
    '45204', '45205', '45311', '45312', '4532', '45401', '45402') THEN 'handel en reparatie van auto s'
    WHEN a.sbi_code in ('46211', '46212', '46213', '46214', '46215', '46216', '46217', '46218', '46219',
    '4622', '46231', '46232', '46241', '46242', '46311', '46312', '4632', '46331', '46332', '4634', '4635',
    '4636', '4637', '46381', '46382', '46383', '46384', '46389', '4639', '46411', '46412', '46421', '46422',
    '46423', '46424', '46425', '46429', '46431', '46432', '46433', '46434', '46435', '46436', '46441',
    '46442', '4645', '46461', '46462', '46471', '46472', '46473', '4648', '46491', '46492', '46493',
    '46494', '46495', '46496', '46497', '46498', '46499', '4651', '4652', '4661', '4662', '4663',
    '4664', '4665', '4666', '46681', '46682', '46691', '46692', '46693', '46694', '46695', '46696',
    '46697', '46699', '46711', '46712', '46713', '46721', '46722', '46723', '46731', '46732', '46733',
    '46734', '46735', '46736', '46737', '46738', '46739', '46741', '46742', '46751', '46752', '46759',
    '46761') THEN 'groothandel (verkoop aan andere ondernemingen, niet zelf vervaardigd)'
    WHEN a.sbi_code in ('0111', '0113', '0116', '0119') THEN 'teelt eenjarige gewassen'
    WHEN a.sbi_code = '0150' THEN 'gemengd bedrijf'
    WHEN a.sbi_code = '0130' THEN 'teelt sierplanten'
    WHEN a.sbi_code in ('0161', '0162', '0163', '0164') THEN 'dienstverlening voor de land/tuinbouw'
    WHEN a.sbi_code in ('0121', '0124', '0125', '0127', '0128', '0129') THEN 'teelt meerjarige gewassen'
    WHEN a.sbi_code in ('0141', '0142', '0143', '0145', '0146', '0147', '0149') THEN 'fokken, houden dieren'
    WHEN a.sbi_code = '9604' THEN 'sauna, solaria'
    WHEN a.sbi_code = '96022' THEN 'schoonheidsverzorging'
    WHEN a.sbi_code in ('96031', '96032') THEN 'uitvaart, crematoria'
    WHEN a.sbi_code in ('96011', '96012', '96013', '9609') THEN 'overige dienstverlening'
    WHEN a.sbi_code =  '96021' THEN 'kappers'
    WHEN a.sbi_code in ('6201', '6202', '6203', '6209') THEN 'activiteiten op het gebied van ict'
    WHEN a.sbi_code in ('59111', '59112', '5912', '5913', '5914', '6010', '6020')
      THEN 'activiteiten  op gebied van film, tv, radio, audio'
    WHEN a.sbi_code in ('6110', '6120', '6130', '6190') THEN 'telecommunicatie'
    WHEN a.sbi_code in ('5811', '5813', '5814', '5819', '5821', '5829', '5920') THEN 'uitgeverijen'
    WHEN a.sbi_code in ('93111', '93112', '93113', '93119', '93121', '93122', '93123', '93124',
    '93125', '93126', '93127', '93128', '93129', '9313', '93141', '93142', '93143', '93144',
    '93145', '93146', '93149', '93151', '93152', '93191', '93192', '93193', '93194', '93195',
    '93196', '93199', '93291') THEN 'sport'
    WHEN a.sbi_code in ('91011', '91012', '91019', '91021', '91022') THEN 'musea, bibliotheken, kunstuitleen'
    WHEN a.sbi_code in ('90011', '90012', '90013', '9002', '9003', '90041', '90042') THEN 'kunst'
    WHEN a.sbi_code in ('55201', '55202', '5530', '93211') THEN 'recreatie'
    WHEN a.sbi_code in ('6810', '68201', '68202', '68203', '68204', '6831', '6832')
      THEN 'verhuur van- en beheer/handel in onroerend goed'
    WHEN a.sbi_code in ('77111', '77112', '7712', '7721', '7722', '77291', '77292', '77299',
    '7731', '7732', '7733', '7734', '7735', '77391', '77399', '7740') THEN 'verhuur van roerende goederen'
    WHEN a.sbi_code in ('6420', '70102') THEN 'holdings'
    WHEN a.sbi_code in ('6411', '64191', '64192', '64193', '64194', '6420', '64301', '64302',
    '64303', '6491', '64921', '64922', '64923', '64924', '6499', '65111', '65112', '65113', '6512',
    '6520', '65301', '65302', '65303', '65309', '6611', '6612', '66191', '66192', '66193', '6621',
    '6622', '66291', '66292', '66293', '66299', '6630') THEN 'financiële dienstverlening en verzekeringen'
    WHEN a.sbi_code in ('94911', '94919', '9492', '94993', '94996') THEN 'idieële organisaties'
    WHEN a.sbi_code in ('9411', '9412', '9420', '94997') THEN 'belangenorganisaties'
    WHEN a.sbi_code in ('0170', '0210', '0220', '0240', '0311', '0312', '0321', '0322',
    '0610', '0620', '0812', '0892', '0893', '0899', '0910', '0990', '3600', '3700',
    '3811', '3812', '3821', '3822', '3831', '3832', '3900', '4110', '5310', '53201',
    '6311', '6312', '6391', '6399', '70101', '7500', '7911', '7912', '7990', '9103',
    '91041', '91042', '92001', '92009', '93212', '93299', '94991', '94994')
        THEN 'overige'
    WHEN a.sbi_code = '94992' THEN 'hobbyclubs'
    WHEN a.sbi_code = '55101' THEN 'hotel-restaurant'
    WHEN a.sbi_code in ('55101', '55102', '5590', '56101', '56102', '5621', '5629', '5630') THEN 'overige horeca'
    WHEN a.sbi_code in ('5621', '5629') THEN 'kantine, catering'
    WHEN a.sbi_code = '56102' THEN 'cafetaria, snackbar, ijssalon'
    WHEN a.sbi_code = '5630' THEN 'café'
    WHEN a.sbi_code = '55102' THEN 'hotel, pension'
    WHEN a.sbi_code = '56101' THEN 'restaurant, café-restaurant'
    ELSE 'overige'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_bouw",
            sql="""
  SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('4120', '42111', '42112', '4212', '4213', '4221', '4222', '4291',
      '4299', '4311', '4312', '4313', '4321', '43221', '43222', '4329', '4331', '4332',
      '4333', '4334', '4339', '4391', '43991', '43992', '43993', '43999') THEN 'bouw overig'
    WHEN a.sbi_code in ('4321', '43221', '43222', '4329') THEN 'bouwinstallatie'
    WHEN a.sbi_code in ('4331', '4332', '4333', '4334', '4339') THEN 'afwerking van gebouwen'
    WHEN a.sbi_code in ('4391', '43991', '43992', '43993', '43999') THEN 'dak- en overige gespecialiseerde bouw'
    WHEN a.sbi_code in ('42111', '42112', '4212', '4213', '4221', '4222', '4291', '4299') THEN 'grond, water, wegenbouw'
    WHEN a.sbi_code = '4120' THEN 'bouw/utiliteitsbouw algemeen / klusbedrijf'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('4120', '42111', '42112', '4212', '4213', '4221', '4222', '4291',
      '4299', '4311', '4312', '4313', '4321', '43221', '43222', '4329', '4331', '4332',
      '4333', '4334', '4339', '4391', '43991', '43992', '43993', '43999', '4321', '43221', '43222', '4329',
      '4331', '4332', '4333', '4334', '4339', '4391', '43991', '43992', '43993', '43999',
      '42111', '42112', '4212', '4213', '4221', '4222', '4291', '4299', '4120')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overheid_onderwijs_zorg",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('85201', '85202', '85203', '85311', '85312', '85313', '85314', '85321', '85322', '85323', '8541',
      '8542', '85511', '85519', '85521', '85522', '8553', '85591', '85592', '85599', '8560') THEN 'onderwijs'
    WHEN a.sbi_code in ('86101', '86102', '86103', '86104', '8621', '86221', '86222', '86231', '86232', '86911',
      '86912', '86913', '86919', '86921', '86922', '86923', '86924', '86925', '86929', '8710', '8720', '87301',
      '87302', '87901', '87902', '88101', '88102', '88103', '88911', '88912', '88991', '88992', '88993', '88999')
        THEN 'gezondheids- en welzijnszorg'
    WHEN a.sbi_code in ('8411', '8412', '8413', '8421', '8422', '84231', '84232', '8424', '8425', '8430') THEN 'overheid'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('85201', '85202', '85203', '85311', '85312', '85313',
    '85314', '85321', '85322', '85323', '8541', '8542', '85511', '85519', '85521', '85522', '8553',
    '85591', '85592', '85599', '8560', '86101', '86102', '86103', '86104', '8621', '86221', '86222', '86231',
    '86232', '86911', '86912', '86913', '86919', '86921', '86922', '86923', '86924', '86925', '86929',
    '8710', '8720', '87301', '87302', '87901', '87902', '88101', '88102', '88103', '88911', '88912',
    '88991', '88992', '88993', '88999', '8411', '8412', '8413', '8421', '8422', '84231', '84232', '8424',
    '8425', '8430')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_productie_installatie_reparatie",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
WHEN a.sbi_code in ('7810', '78201', '78202', '78203', '7830') THEN 'arbeidsbemiddeling, uitzendbureaus, uitleenbureaus'
    WHEN a.sbi_code in ('74201', '74202', '74203', '7430', '7490', '8010', '8020', '8030', '8110', '8121',
    '81221', '81222', '81229', '8129', '8130', '8211', '8219', '8220', '8230', '8291', '8292', '82991',
    '82992', '82999') THEN 'overige zakelijke dienstverlening'
    WHEN a.sbi_code in ('7311', '7312', '7320') THEN 'reclame en marktonderzoek'
    WHEN a.sbi_code = '71112' THEN 'interieurarchitecten'
    WHEN a.sbi_code in ('70221', '70222') THEN 'managementadvies, economisch advies'
    WHEN a.sbi_code in ('7112', '71201', '71202', '71203', '72111', '72112', '72113', '72191',
    '72192', '72193', '72199', '7220') THEN 'technisch ontwerp, advies, keuring/research'
    WHEN a.sbi_code in ('74101', '74102', '74103') THEN 'design'
    WHEN a.sbi_code = '7021' THEN 'public relationsbureaus'
    WHEN a.sbi_code in ('69101', '69102', '69103', '69104', '69105') THEN 'advocaten rechtskundige diensten, notarissen'
    WHEN a.sbi_code = '71111' THEN 'architecten'
    WHEN a.sbi_code in ('69201', '69202', '69203', '69204', '69209') THEN 'accountancy, administratie'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('7810', '78201', '78202', '78203', '7830',
    '74201', '74202', '74203', '7430', '7490', '8010', '8020', '8030', '8110', '8121',
    '81221', '81222', '81229', '8129', '8130', '8211', '8219', '8220', '8230', '8291', '8292', '82991',
    '82992', '82999', '7311', '7312', '7320', '71112', '70221', '70222', '7112', '71201', '71202', '71203',
    '72111', '72112', '72113', '72191', '72192', '72193', '72199', '7220', '74101', '74102', '74103', '7021',
    '69101', '69102', '69103', '69104', '69105', '71111', '69201', '69202', '69203', '69204', '69209')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_handel_vervoer_opslag",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('4910', '4920', '4931', '4932', '49391', '49392', '49393', '4941', '4942',
    '4950', '5010', '50201', '50202', '5030', '50401', '50402', '50403', '5110', '5121', '53202') THEN 'vervoer'
    WHEN a.sbi_code in ('4711', '47191', '47192', '4721', '47221', '47222', '4723', '47241',
    '47242', '4725', '4726', '47291', '47292', '47293', '47299', '4730', '4741', '4742', '47431',
    '47432', '47511', '47512', '47513', '47521', '47522', '47523', '47524', '47525', '47526',
    '47527', '47528', '4753', '47541', '47542', '47543', '47544', '47591', '47592', '47593',
    '47594', '47595', '47596', '47597', '4761', '4762', '4763', '47641', '47642', '47643', '47644',
    '4765', '47711', '47712', '47713', '47714', '47715', '47716', '47717', '47718', '47721', '47722',
    '4773', '47741', '47742', '4775', '47761', '47762', '47763', '4777', '47781', '47782', '47783',
    '47789', '47791', '47792', '47793', '47811', '47819', '4782', '47891', '47892', '47899', '47911',
    '47912', '47913', '47914', '47915', '47916', '47918', '47919', '47991', '47992', '47999')
      THEN 'detailhandel (verkoop aan consumenten, niet zelf vervaardigd)'
    WHEN a.sbi_code in ('4611', '4612', '4613', '4614', '4615', '4616', '4617', '4618', '4619')
      THEN 'handelsbemiddeling (tussenpersoon, verkoopt niet zelf)'
    WHEN a.sbi_code in ('52101', '52102', '52109') THEN 'opslag'
    WHEN a.sbi_code in ('5221', '5222', '5223', '52241', '52242', '52291', '52292') THEN 'dienstverlening vervoer'
    WHEN a.sbi_code in ('45111', '45112', '45191', '45192', '45193', '45194', '45201', '45202', '45203',
    '45204', '45205', '45311', '45312', '4532', '45401', '45402') THEN 'handel en reparatie van auto s'
    WHEN a.sbi_code in ('46211', '46212', '46213', '46214', '46215', '46216', '46217', '46218', '46219',
    '4622', '46231', '46232', '46241', '46242', '46311', '46312', '4632', '46331', '46332', '4634', '4635',
    '4636', '4637', '46381', '46382', '46383', '46384', '46389', '4639', '46411', '46412', '46421', '46422',
    '46423', '46424', '46425', '46429', '46431', '46432', '46433', '46434', '46435', '46436', '46441',
    '46442', '4645', '46461', '46462', '46471', '46472', '46473', '4648', '46491', '46492', '46493',
    '46494', '46495', '46496', '46497', '46498', '46499', '4651', '4652', '4661', '4662', '4663',
    '4664', '4665', '4666', '46681', '46682', '46691', '46692', '46693', '46694', '46695', '46696',
    '46697', '46699', '46711', '46712', '46713', '46721', '46722', '46723', '46731', '46732', '46733',
    '46734', '46735', '46736', '46737', '46738', '46739', '46741', '46742', '46751', '46752', '46759',
    '46761') THEN 'groothandel (verkoop aan andere ondernemingen, niet zelf vervaardigd)'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('4910', '4920', '4931', '4932', '49391', '49392',
    '49393', '4941', '4942', '4950', '5010', '50201', '50202', '5030', '50401', '50402', '50403',
    '5110', '5121', '53202', '4711', '47191', '47192', '4721', '47221', '47222', '4723', '47241',
    '47242', '4725', '4726', '47291', '47292', '47293', '47299', '4730', '4741', '4742', '47431',
    '47432', '47511', '47512', '47513', '47521', '47522', '47523', '47524', '47525', '47526',
    '47527', '47528', '4753', '47541', '47542', '47543', '47544', '47591', '47592', '47593',
    '47594', '47595', '47596', '47597', '4761', '4762', '4763', '47641', '47642', '47643', '47644',
    '4765', '47711', '47712', '47713', '47714', '47715', '47716', '47717', '47718', '47721', '47722',
    '4773', '47741', '47742', '4775', '47761', '47762', '47763', '4777', '47781', '47782', '47783',
    '47789', '47791', '47792', '47793', '47811', '47819', '4782', '47891', '47892', '47899', '47911',
    '47912', '47913', '47914', '47915', '47916', '47918', '47919', '47991', '47992', '47999',
    '4611', '4612', '4613', '4614', '4615', '4616', '4617', '4618', '4619', '52101', '52102', '52109',
    '5221', '5222', '5223', '52241', '52242', '52291', '52292', '45111', '45112', '45191', '45192',
    '45193', '45194', '45201', '45202', '45203', '45204', '45205', '45311', '45312', '4532', '45401',
    '45402', '46211', '46212', '46213', '46214', '46215', '46216', '46217', '46218', '46219',
    '4622', '46231', '46232', '46241', '46242', '46311', '46312', '4632', '46331', '46332', '4634', '4635',
    '4636', '4637', '46381', '46382', '46383', '46384', '46389', '4639', '46411', '46412', '46421', '46422',
    '46423', '46424', '46425', '46429', '46431', '46432', '46433', '46434', '46435', '46436', '46441',
    '46442', '4645', '46461', '46462', '46471', '46472', '46473', '4648', '46491', '46492', '46493',
    '46494', '46495', '46496', '46497', '46498', '46499', '4651', '4652', '4661', '4662', '4663',
    '4664', '4665', '4666', '46681', '46682', '46691', '46692', '46693', '46694', '46695', '46696',
    '46697', '46699', '46711', '46712', '46713', '46721', '46722', '46723', '46731', '46732', '46733',
    '46734', '46735', '46736', '46737', '46738', '46739', '46741', '46742', '46751', '46752', '46759',
    '46761')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_landbouw",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('0111', '0113', '0116', '0119') THEN 'teelt eenjarige gewassen'
    WHEN a.sbi_code = '0150' THEN 'gemengd bedrijf'
    WHEN a.sbi_code = '0130' THEN 'teelt sierplanten'
    WHEN a.sbi_code in ('0161', '0162', '0163', '0164') THEN 'dienstverlening voor de land/tuinbouw'
    WHEN a.sbi_code in ('0121', '0124', '0125', '0127', '0128', '0129') THEN 'teelt meerjarige gewassen'
    WHEN a.sbi_code in ('0141', '0142', '0143', '0145', '0146', '0147', '0149') THEN 'fokken, houden dieren'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('0111', '0113', '0116', '0119' ,'0150','0130','0121', '0124',
    '0125', '0127', '0128', '0129', '0141', '0142', '0143', '0145', '0146', '0147', '0149')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_persoonlijke_dienstverlening",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code = '9604' THEN 'sauna, solaria'
    WHEN a.sbi_code = '96022' THEN 'schoonheidsverzorging'
    WHEN a.sbi_code in ('96031', '96032') THEN 'uitvaart, crematoria'
    WHEN a.sbi_code in ('96011', '96012', '96013', '9609') THEN 'overige dienstverlening'
    WHEN a.sbi_code =  '96021' THEN 'kappers'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('9604', '96022', '96031', '96032', '96011',
    '96012', '96013', '9609', ' 96021')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_informatie_telecommunicatie",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('6201', '6202', '6203', '6209') THEN 'activiteiten op het gebied van ict'
    WHEN a.sbi_code in ('59111', '59112', '5912', '5913', '5914', '6010', '6020')
      THEN 'activiteiten  op gebied van film, tv, radio, audio'
    WHEN a.sbi_code in ('6110', '6120', '6130', '6190') THEN 'telecommunicatie'
    WHEN a.sbi_code in ('5811', '5813', '5814', '5819', '5821', '5829', '5920') THEN 'uitgeverijen'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('6201', '6202', '6203', '6209', '59111', '59112', '5912',
    '5913', '5914', '6010', '6020', '6110', '6120', '6130', '6190', '5811', '5813', '5814', '5819', '5821',
    '5829', '5920')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_cultuur_sport_recreatie",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('93111', '93112', '93113', '93119', '93121', '93122', '93123', '93124',
    '93125', '93126', '93127', '93128', '93129', '9313', '93141', '93142', '93143', '93144',
    '93145', '93146', '93149', '93151', '93152', '93191', '93192', '93193', '93194', '93195',
    '93196', '93199', '93291') THEN 'sport'
    WHEN a.sbi_code in ('91011', '91012', '91019', '91021', '91022') THEN 'musea, bibliotheken, kunstuitleen'
    WHEN a.sbi_code in ('90011', '90012', '90013', '9002', '9003', '90041', '90042') THEN 'kunst'
    WHEN a.sbi_code in ('55201', '55202', '5530', '93211') THEN 'recreatie'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('93111', '93112', '93113', '93119', '93121',
    '93122', '93123', '93124', '93125', '93126', '93127', '93128', '93129', '9313', '93141',
    '93142', '93143', '93144', '93145', '93146', '93149', '93151', '93152', '93191', '93192',
    '93193', '93194', '93195', '93196', '93199', '93291', '91011', '91012', '91019', '91021',
    '91022', '90011', '90012', '90013', '9002', '9003', '90041', '90042', '55201', '55202',
    '5530', '93211')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('6810', '68201', '68202', '68203', '68204', '6831', '6832')
      THEN 'verhuur van- en beheer/handel in onroerend goed'
    WHEN a.sbi_code in ('77111', '77112', '7712', '7721', '7722', '77291', '77292', '77299',
    '7731', '7732', '7733', '7734', '7735', '77391', '77399', '7740') THEN 'verhuur van roerende goederen'
    WHEN a.sbi_code in ('6420', '70102') THEN 'holdings'
    WHEN a.sbi_code in ('6411', '64191', '64192', '64193', '64194', '6420', '64301', '64302',
    '64303', '6491', '64921', '64922', '64923', '64924', '6499', '65111', '65112', '65113', '6512',
    '6520', '65301', '65302', '65303', '65309', '6611', '6612', '66191', '66192', '66193', '6621',
    '6622', '66291', '66292', '66293', '66299', '6630') THEN 'financiële dienstverlening en verzekeringen'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('6810', '68201', '68202', '68203', '68204', '6831',
    '6832', '77111', '77112', '7712', '7721', '7722', '77291', '77292', '77299',
    '7731', '7732', '7733', '7734', '7735', '77391', '77399', '7740', '6420', '70102',
    '6411', '64191', '64192', '64193', '64194', '6420', '64301', '64302',
    '64303', '6491', '64921', '64922', '64923', '64924', '6499', '65111', '65112', '65113', '6512',
    '6520', '65301', '65302', '65303', '65309', '6611', '6612', '66191', '66192', '66193', '6621',
    '6622', '66291', '66292', '66293', '66299', '6630')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overige",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code in ('94911', '94919', '9492', '94993', '94996') THEN 'idieële organisaties'
    WHEN a.sbi_code in ('9411', '9412', '9420', '94997') THEN 'belangenorganisaties'
    WHEN a.sbi_code in ('0170', '0210', '0220', '0240', '0311', '0312', '0321', '0322',
    '0610', '0620', '0812', '0892', '0893', '0899', '0910', '0990', '3600', '3700',
    '3811', '3812', '3821', '3822', '3831', '3832', '3900', '4110', '5310', '53201',
    '6311', '6312', '6391', '6399', '70101', '7500', '7911', '7912', '7990', '9103',
    '91041', '91042', '92001', '92009', '93212', '93299', '94991', '94994')
        THEN 'overige'
    WHEN a.sbi_code = '94992' THEN 'hobbyclubs'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('94911', '94919', '9492', '94993', '94996',
    '9411', '9412', '9420', '94997', '0170', '0210', '0220', '0240', '0311', '0312', '0321', '0322',
    '0610', '0620', '0812', '0892', '0893', '0899', '0910', '0990', '3600', '3700',
    '3811', '3812', '3821', '3822', '3831', '3832', '3900', '4110', '5310', '53201',
    '6311', '6312', '6391', '6399', '70101', '7500', '7911', '7912', '7990', '9103',
    '91041', '91042', '92001', '92009', '93212', '93299', '94991', '94994', '94992')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_horeca",
            sql="""
SELECT ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE
    WHEN vs.bezoekadres_id NOTNULL THEN 'B'
    WHEN vs.postadres_id NOTNULL THEN 'P'
    ELSE 'V'
  END as locatie_type,
  loc.geometrie as geometrie,
  CAST('handelsregister/vestiging' AS text),
  CASE
    WHEN a.sbi_code = '55101' THEN 'hotel-restaurant'
    WHEN a.sbi_code in ('55101', '55102', '5590', '56101', '56102', '5621', '5629', '5630') THEN 'overige horeca'
    WHEN a.sbi_code in ('5621', '5629') THEN 'kantine, catering'
    WHEN a.sbi_code = '56102' THEN 'cafetaria, snackbar, ijssalon'
    WHEN a.sbi_code = '5630' THEN 'café'
    WHEN a.sbi_code = '55102' THEN 'hotel, pension'
    WHEN a.sbi_code = '56101' THEN 'restaurant, café-restaurant'
    END as sbi_detailgroep,
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id AND a.sbi_code in ('55101', '55101', '55102', '5590', '56101',
    '56102', '5621', '5629', '5630', '5621', '5629', '56102', '5630', '55102', '56101')
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie),
    django_site site
WHERE site.name = 'API Domain'
"""
        ),

    ]
