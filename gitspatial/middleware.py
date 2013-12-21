from django.contrib.auth.models import User


class ImpersonateMiddleware(object):
    def process_request(self, request):
        if request.user.is_superuser and '__impersonate' in request.GET:
            request.session['impersonate_id'] = int(request.GET['__impersonate'])
        elif '__unimpersonate' in request.GET and 'impersonate_id' in request.session:
            del request.session['impersonate_id']
        if request.user.is_superuser and 'impersonate_id' in request.session:
            request.user = User.objects.get(id=request.session['impersonate_id'])