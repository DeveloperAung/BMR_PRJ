from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

def verify_google_id_token(token: str) -> dict:
    req = requests.Request()
    info = id_token.verify_oauth2_token(token, req, settings.GOOGLE_OAUTH_AUDIENCE or None)
    return info
