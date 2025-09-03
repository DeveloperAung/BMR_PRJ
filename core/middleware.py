import threading
from django.utils.deprecation import MiddlewareMixin

_local  = threading.local()

def get_current_user():
    return getattr(_local , "user", None)

class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _local .user = getattr(request, "user", None)

    def process_response(self, request, response):
        _local .user = None
        return response
