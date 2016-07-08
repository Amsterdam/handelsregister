from django.contrib.gis.db import models
# Create your models here.


class Persoon(models.Model):
    """
    """
    rechtsvorm = models.CharField(max_length=50, blank=True, null=True)
    uitgebreiderechtsvorm = models.CharField(
        max_length=240, blank=True, null=True)

    volledigenaam = models.CharField(max_length=240, blank=True, null=True)

    # locatie

    # bezoekadres
    # postadres
    # bezoekadres

    # BeperkingRechtsHandeling (BIR)

    # BijzondereRechtstoestand(BRT)

    # Schuldsanering SSN

    # SurseanceVanBetaling SUR

    # Faillisement (FAL)



class NatuurlijkPersoon(models.Model):
    """
    NPS
    """
    pass


class NietNatuurlijkPersoon(models.Model):
    """
    NNP
    """
    pass


class BuitenlandseVennootschap(models.Model):
    """
    BRV
    """
    pass


class BuitenlandseNietNatuurlijkPersoon(models.Model):
    """
    BRV
    """
    pass


class FunctieVervulling(models.Model):
    """
    BRV
    """
    pass


class Activiteit(models.Model):
    """
    ACT
    """


class MaatschappelijkActiviteit(models.Model):
    """
    MAC
    """


class Vestiging(models.Model):
    """
    VES
    """


class Locatie(models.Model):
    """
    LOC
    """
    pass


class Handelsnaam(models.Model):
    """
    HN
    """
    pass


class CommunicatieGegevens(models.Model):
    """
    COM
    """


class RechterlijkeUitspraak(models.Model):
    """
    UIT
    """


class Kapitaal(models.Model):
    """
    KAP
    """
    pass
