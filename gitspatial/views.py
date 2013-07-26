from django.shortcuts import render


def home(request):
    """
    GET /

    Show the home page
    """
    return render(request, 'index.html')
