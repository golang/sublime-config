# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import sys


if sys.version_info >= (3,):
    from imp import reload

if 'golangconfig.dev.mocks' in sys.modules:
    reload(sys.modules['golangconfig.dev.mocks'])
if 'golangconfig' in sys.modules:
    reload(sys.modules['golangconfig'])
