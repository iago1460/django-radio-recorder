import sys

if sys.version_info < (3, 7):
    raise RuntimeError('Python 3.7 or later is required')

__version__ = '1.0'
