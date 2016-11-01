
from django.db import migrations
from geo_views import migrate
from django.conf import settings
from django.contrib.sites.models import Site


def create_site(apps, *args, **kwargs):
    pass

def delete_site(apps, *args, **kwargs):
    migrations.DeleteModel('DataSelectieView')
    migrations.DeleteModel('SbicodesPerVestiging')
    migrations.DeleteModel('BetrokkenPersonen')


class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0007_dataselectie'),
    ]

    operations = [
        # set the site name
        migrations.RunPython(code=create_site, reverse_code=delete_site),
        # create the hr views
        migrate.ManageView(
            view_name="hr_betrokken_personen",
            sql="""
 SELECT row_number() OVER (ORDER BY (( SELECT 1))) AS id,
    mac.naam AS mac_naam,
    mac.kvk_nummer,
    vs.id AS vestiging_id,
    vs.vestigingsnummer,
    p1.id AS persoons_id,
    p1.rol,
        CASE
            WHEN p1.naam IS NOT NULL THEN p1.naam
            WHEN p2.naam IS NOT NULL THEN p2.naam
            WHEN np1.geslachtsnaam IS NOT NULL THEN np1.geslachtsnaam
            ELSE NULL::character varying
        END AS naam,
    p1.rechtsvorm,
    fv.functietitel,
    fv.soortbevoegdheid,
    np2.geslachtsnaam AS bevoegde_naam
   FROM hr_maatschappelijkeactiviteit mac
     JOIN hr_vestiging vs ON vs.maatschappelijke_activiteit_id = mac.id
     JOIN hr_persoon p1 ON mac.eigenaar_id = p1.id
     LEFT JOIN hr_natuurlijkpersoon np1 ON np1.id::text = p1.natuurlijkpersoon_id::text
     LEFT JOIN hr_functievervulling fv ON fv.heeft_aansprakelijke_id = mac.eigenaar_id
     LEFT JOIN hr_persoon p2 ON fv.is_aansprakelijke_id = p2.id
     LEFT JOIN hr_natuurlijkpersoon np2 ON np2.id::text = p2.natuurlijkpersoon_id::text
    """),
        migrate.ManageView(
            view_name="hr_sbicodes_per_vestiging",
            sql="""
 SELECT
 row_number() OVER (ORDER BY (( SELECT 1))) AS id,
 hr_a.vestiging_id,
    a.sbi_code,
    a.activiteitsomschrijving,
    sc.subcategorie,
    hc.hcat,
    sc.scat,
    hc.hoofdcategorie,
    sbi.sub_sub_categorie
   FROM hr_vestiging_activiteiten hr_a
     JOIN hr_activiteit a ON a.id::text = hr_a.activiteit_id::text
     JOIN hr_cbs_sbicodes sbi ON a.sbi_code::text = sbi.sbi_code::text
     JOIN hr_cbs_sbi_subcat sc ON sbi.scat_id::text = sc.scat::text
     JOIN hr_cbs_sbi_hoofdcat hc ON sc.hcat_id::text = hc.hcat::text
       """),
        migrate.ManageView(
            view_name="hr_dataselectieview",
            sql="""
 SELECT
    row_number() OVER (ORDER BY (( SELECT 1))) AS id,
    vs.vestigingsnummer,
    vs.id AS vestiging_id,
    vs.naam,
    ((site.domain::text || 'handelsregister/vestiging/'::text) || vs.vestigingsnummer::text) || '/'::text AS uri,
    vs.hoofdvestiging,
        CASE
            WHEN vs.bezoekadres_id IS NOT NULL THEN 'B'::text
            WHEN vs.postadres_id IS NOT NULL THEN 'P'::text
            ELSE 'V'::text
        END AS locatie_type,
    vs.bezoekadres_id,
    vs.postadres_id,
    loc.geometrie,
    mac.kvk_nummer,
    mac.datum_aanvang,
    mac.datum_einde,
        CASE
            WHEN hnm.handelsnaam IS NOT NULL THEN hnm.handelsnaam
            ELSE hnv.handelsnaam
        END AS handelsnaam
   FROM hr_vestiging vs
     JOIN hr_locatie loc ON (vs.bezoekadres_id::text = loc.id::text OR vs.postadres_id::text = loc.id::text) AND st_isvalid(loc.geometrie)
     JOIN hr_maatschappelijkeactiviteit mac ON vs.maatschappelijke_activiteit_id = mac.id
     LEFT JOIN ( SELECT t1.onderneming_id,
            t1.handelsnaam_id
           FROM hr_onderneming_handelsnamen t1
          WHERE t1.id = (( SELECT max(t2.id) AS max
                   FROM hr_onderneming_handelsnamen t2
                  WHERE t1.onderneming_id::text = t2.onderneming_id::text))) hom ON hom.onderneming_id::text = mac.onderneming_id::text
     LEFT JOIN hr_handelsnaam hnm ON hnm.id::text = hom.handelsnaam_id::text
     LEFT JOIN hr_vestiging_handelsnamen hvh ON hvh.vestiging_id::text = vs.vestigingsnummer::text
     LEFT JOIN hr_handelsnaam hnv ON hnv.id::text = hvh.handelsnaam_id::text,
    django_site site
  WHERE site.name::text = 'API Domain'::text;""")
        ]
