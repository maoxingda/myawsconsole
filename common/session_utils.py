from django.conf import settings


def post_data_to_session(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == "POST":
            for key, value in request.POST.items():
                if key != "csrfmiddlewaretoken":
                    request.session[key + settings.SESSION_VAR_SUFFIX] = value
        return view_func(request, *args, **kwargs)

    return wrapper
