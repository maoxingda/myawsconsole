from django.http import HttpResponseRedirect


class HttpResponseRedirectToReferrer(HttpResponseRedirect):
    def __init__(self, request, *args, **kwargs):
        redirect_to = request.META.get("HTTP_REFERER", "/")
        super().__init__(redirect_to, *args, **kwargs)
