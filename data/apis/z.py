import os
from dotenv import load_dotenv


load_dotenv()

_Z_URL = os.getenv("zURL")
_Z_INSTANCIA = os.getenv("zIns")
_Z_TOKEN = os.getenv("zToken")
_S_Z_TOKEN = os.getenv("segzToken")

def get_url():
    return _Z_URL

def get_instancia():
    return _Z_INSTANCIA

def get_token():
    return _Z_TOKEN

def get_s_token():
    return _S_Z_TOKEN