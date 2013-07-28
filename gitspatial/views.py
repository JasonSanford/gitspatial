import logging

from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

#from .tasks import wait


logger = logging.getLogger(__name__)


def home(request):
    """
    GET /

    Show the home page
    """
    #wait.apply_async(duration=60)
    return render(request, 'index.html')


def logout(request):
    """
    GET /logout/

    Log the current user out
    """
    auth_logout(request)
    return redirect('gitspatial.views.home')


@login_required
def user_landing(request):
    """
    GET /user/

    User landing page
    """
    return render(request, 'user.html')
