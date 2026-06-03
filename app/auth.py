import msal
import requests
from flask import current_app

def build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        current_app.config['MICROSOFT_CLIENT_ID'],
        authority=current_app.config['MICROSOFT_AUTHORITY'],
        client_credential=current_app.config['MICROSOFT_CLIENT_SECRET'],
        token_cache=cache
    )

def get_auth_url(scopes=None):
    if scopes is None:
        scopes = ["User.Read"]
    msal_app = build_msal_app()
    return msal_app.get_authorization_request_url(
        scopes,
        redirect_uri=current_app.config['MICROSOFT_REDIRECT_URI']
    )

def get_token_from_code(code, scopes=None):
    if scopes is None:
        scopes = ["User.Read"]
    msal_app = build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=scopes,
        redirect_uri=current_app.config['MICROSOFT_REDIRECT_URI']
    )
    return result

def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None
