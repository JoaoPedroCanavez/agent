import os
from dotenv import load_dotenv


load_dotenv()

_EVO_URL = os.getenv("evoURL")
_EVO_INSTANCIA = os.getenv("evoIns")
_EVO_TOKEN = os.getenv("evoToken")

def get_url():
    return _EVO_URL

def get_instancia():
    return _EVO_INSTANCIA

def get_token():
    return _EVO_TOKEN