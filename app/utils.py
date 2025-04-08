import jcs
from multiformats import multibase, multihash
import urllib.parse


def url_encode(value):
    return urllib.parse.quote(value, safe='')

def force_array(value):
    return value if isinstance(value, list) else [value]

def digest_multibase(value):
    return multibase.encode(multihash.digest(jcs.canonicalize(value), "sha2-256"), "base58btc")

def id_to_url(identifier):
    return 'https://'+'/'.join(identifier.split(':')[3:])