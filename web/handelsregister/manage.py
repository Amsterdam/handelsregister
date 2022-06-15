#!/usr/bin/env python

import logging

import os
import sys

log = logging.getLogger(__name__)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "handelsregister.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
