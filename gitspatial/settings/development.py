from defaults import *

STATIC_URL = '/static/'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['gitspatial']['level'] = 'DEBUG'
