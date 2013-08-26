from django.shortcuts import redirect


def api_landing(request):
    return redirect('v1_api_docs')
