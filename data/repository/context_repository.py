import logging
from data.apis import sup
from supabase import create_client, Client
from postgrest.exceptions import APIError
from typing import List, Dict, Union

logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class Banco:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.client: Client = create_client(sup.get_instancia(), sup.get_key())
#--------------------------------------------------------------------------------------------------------------------#
    def busca_id_por_numero(self, numero: str) -> Union[int, None]:
        try:
            dados_busca = self.client.table('usr').select("id").eq('numero', numero).execute().data

            if dados_busca:
                logger.info(f"Usuário {numero} encontrado. ID: {dados_busca[0]['id']}")
                return dados_busca[0]['id']
        except Exception as e:
            logger.error(f"Erro na busca inicial no Supabase: {e}")

        logger.info(f"Usuário {numero} não encontrado. Tentando criar novo registro.")
        try:
            novo_registro = {'numero': numero,}
            response_insert = self.client.table('usr').insert(novo_registro).execute()
            
            novo_id = response_insert.data[0]['id']
            logger.info(f"Novo usuário {numero} criado com sucesso. ID: {novo_id}")
            return novo_id
        except APIError as e:
            logger.error(f"Erro ao inserir novo usuário: {e}")
            return None
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado na inserção: {e}")
            return None
#--------------------------------------------------------------------------------------------------------------------#    
    def get_messages(self, user_id: int) -> List[Dict]:
        try: 
            cnxt_data = (self.client
                         .table('mensagens_salvas')
                         .select('role, msg') 
                         .eq('usr_id', user_id)
                         .order('created_at', desc=True) 
                         .limit(5) 
                         .execute()).data
            cnxt_data.reverse()
            
            contexto_formatado = []
            for item in cnxt_data:
                 contexto_formatado.append({'role': item['role'],'content': item['msg']})
            return contexto_formatado
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto do Supabase para ID {user_id}: {e}", exc_info=True)
            return []
#--------------------------------------------------------------------------------------------------------------------#
    def adiciona_mensagem(self, user_id: int, role: str, mensagem: str):
        try:
            novo_registro_msg = {'usr_id': user_id,'role': role,'msg': mensagem}
            self.client.table('mensagens_salvas').insert(novo_registro_msg).execute()
             
            logger.info(f"Mensagem de '{role}' salva com sucesso para ID {user_id}.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem no Supabase para ID {user_id}: {e}", exc_info=True)
            return False
#--------------------------------------------------------------------------------------------------------------------#
