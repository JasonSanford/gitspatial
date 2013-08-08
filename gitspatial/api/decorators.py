from functools import wraps


def jsonp(f):
    @wraps(f)
    def jsonp_wrapper(request, *args, **kwargs):
        resp = f(request, *args, **kwargs)
        #if resp.status_code != 200:
        #    return resp
        if 'callback' in request.GET:
            callback = request.GET['callback']
            resp['Content-Type'] = 'text/javascript'
            resp.content = "%s(%s)" % (callback, resp.content)
            return resp
        else:
            return resp
    return jsonp_wrapper
