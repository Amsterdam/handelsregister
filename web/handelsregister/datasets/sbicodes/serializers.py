"""
SBI codes
"""

from .models import SBICodeHierarchy
from datapunt_api import rest


class SBICodeHierarchySerializer(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = SBICodeHierarchy

        fields = (
            '_display',
            '_links',
            'title',
            'code',
        )


class SBICodeHierarchyDetailsSerializer(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = SBICodeHierarchy

        fields = (
            '_display',
            '_links',
            'title',
            'code',
            'sbi_tree',
            'qa_tree',
        )
