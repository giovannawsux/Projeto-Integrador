import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app


class SuapAuthenticationService:
    @staticmethod
    def authorization_url(state, redirect_uri):
        params = urlencode({
            'response_type': 'code',
            'client_id': current_app.config['SUAP_CLIENT_ID'],
            'redirect_uri': redirect_uri,
            'state': state,
        })
        return f"{current_app.config['SUAP_URL']}/o/authorize/?{params}"

    @classmethod
    def exchange_code(cls, code, redirect_uri):
        data = urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': current_app.config['SUAP_CLIENT_ID'],
            'client_secret': current_app.config['SUAP_CLIENT_SECRET'],
        }).encode()
        request = Request(
            f"{current_app.config['SUAP_URL']}/o/token/",
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            },
        )
        try:
            with urlopen(request) as response:
                return json.load(response)
        except (HTTPError, URLError):
            return None

    @classmethod
    def eu(cls, access_token):
        request = Request(
            f"{current_app.config['SUAP_URL']}/api/rh/meus-dados/",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            },
        )
        try:
            with urlopen(request) as response:
                return json.load(response)
        except (HTTPError, URLError):
            return None