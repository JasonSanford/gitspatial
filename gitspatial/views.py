import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def home(request):
    """
    GET /

    Show the home page
    """
    logger.error('Error at home')
    return render(request, 'index.html')
