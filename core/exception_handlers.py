from rest_framework.views import exception_handler
from .responses import fail

def enveloped_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    return fail(error=response.data, message="Request failed", status=response.status_code)
