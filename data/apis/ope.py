import os
from dotenv import load_dotenv

load_dotenv

_GPT_KEY = os.getenv('openAIKey')

def get_key():
    return _GPT_KEY 