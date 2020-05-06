import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'mycoffeeshop.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    try:
        token = request.headers.get('Authorization')
        if token:
            token_type = token.split(' ')[0]
            if(token_type == 'Bearer' and len(token.split(' ')) == 2):
                token = token.split(' ')[1]
                return token
            elif(len(token.split(' ')) > 2):
                raise AuthError({
                    'error' : 'Invalid header!',
                    'status_code' : 401
                }, 401)
        else:
            raise AuthError({
                'error' : 'Header malformed!',
                'status_code' : 401
            },401)
    except:
        raise AuthError({
                'error' : 'No authorization header!',
                'status_code' : 401
            }, 401) 

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    try: 
        permission in payload['permissions']
    except:
        raise AuthError({'error' : 'Not authorised to access','status_code' : 403}, 403)

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    auth0_url_keys = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    keysStr = auth0_url_keys.read().decode('utf-8')
    keysObj = json.loads(keysStr)

    header_token = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in header_token:
        raise AuthError({
            'error' : 'Invalid Header',
            'status_code' : 401
        },401)
    else : 
        keys = keysObj['keys']
        for key in keys:
            if(key['kid'] == header_token['kid']):
                rsa_key['kid'] = key['kid']
                rsa_key['kty'] = key['kty']
                rsa_key['use'] = key['use']
                rsa_key['n'] = key['n']
                rsa_key['e'] = key['e']
        
    if rsa_key:
        try:
            payload = jwt.decode(token, rsa_key, algorithms=ALGORITHMS,audience=API_AUDIENCE,issuer=f'https://{AUTH0_DOMAIN}/')
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'error': 'Token expired',
                'status_code': 401
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'status_code': 401,
                'error': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except:
            raise AuthError({'error' : 'Unable to parse header', 'status_code' : 400}, 400)
'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator