
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField


class SBICodeHierarchy(models.Model):

    code = models.CharField(
        max_length=8,
        primary_key=True
    )

    title = models.TextField()

    sbi_tree = JSONField()

    qa_tree = JSONField(null=True)
