import urllib.parse
import base64
import json


def url_encode(value):
    return urllib.parse.quote(value, safe='')

def decode_jwt_vc(jwt_vc):
    jwt_payload = jwt_vc.split('.')[1]
    credential = base64.b64decode(jwt_payload, '-_').decode()
    return json.loads(credential)
