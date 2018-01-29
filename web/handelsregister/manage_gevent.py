#!/usr/bin/env python
from gevent import monkey
monkey.patch_all(thread=False, select=False)

import logging
import os
import sys

log = logging.getLogger(__name__)

log.info('NOTE: gevent is loaded.')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "handelsregister.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
