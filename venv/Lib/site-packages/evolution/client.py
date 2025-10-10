import requests
from .exceptions import EvolutionAuthenticationError, EvolutionNotFoundError, EvolutionAPIError
from .services.instance import InstanceService
from .services.instance_operations import InstanceOperationsService
from .services.message import MessageService
from .services.call import CallService
from .services.chat import ChatService
from .services.label import LabelService
from .services.profile import ProfileService
from .services.group import GroupService
class EvolutionClient:
    """
    Cliente para interagir com a API Evolution.

    Args:
        base_url (str): A URL base do servidor da API Evolution.
        api_token (str): O token de autenticação para acessar a API.
    """

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.instances = InstanceService(self)
        self.instance_operations = InstanceOperationsService(self)
        self.messages = MessageService(self)
        self.calls = CallService(self)
        self.chat = ChatService(self)
        self.label = LabelService(self)
        self.profile = ProfileService(self)
        self.group = GroupService(self)
        
    def _get_headers(self, instance_token: str = None):
        return {
            'apikey': instance_token or self.api_token,
            'Content-Type': 'application/json'
        }

    def _get_full_url(self, endpoint):
        return f'{self.base_url}/{endpoint}'

    def _handle_response(self, response):
        if response.status_code == 401:
            raise EvolutionAuthenticationError('Falha na autenticação.')
        elif response.status_code == 404:
            raise EvolutionNotFoundError('Recurso não encontrado.')
        elif response.ok:
            try:
                return response.json()
            except ValueError:
                return response.content
        else:
            error_detail = ''
            try:
                error_detail = f' - {response.json()}'
            except:
                error_detail = f' - {response.text}'
            raise EvolutionAPIError(f'Erro na requisição: {response.status_code}{error_detail}')

    def get(self, endpoint: str, instance_token: str = None):
        """Faz uma requisição GET."""
        url = self._get_full_url(endpoint)
        response = requests.get(url, headers=self._get_headers(instance_token))
        return self._handle_response(response)

    def post(self, endpoint: str, data: dict = None, instance_token: str = None):
        """Faz uma requisição POST."""
        url = self._get_full_url(endpoint)
        response = requests.post(url, headers=self._get_headers(instance_token), json=data)
        return self._handle_response(response)

    def put(self, endpoint, data=None):
        """Faz uma requisição PUT."""
        url = self._get_full_url(endpoint)
        response = requests.put(url, headers=self.headers, json=data)
        return self._handle_response(response)

    def delete(self, endpoint: str, instance_token: str = None):
        """Faz uma requisição DELETE."""
        url = self._get_full_url(endpoint)
        response = requests.delete(url, headers=self._get_headers(instance_token))
        return self._handle_response(response)
