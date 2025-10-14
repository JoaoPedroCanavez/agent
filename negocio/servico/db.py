import logging
from data.apis import sup
from supabase import create_client, Client
from postgrest.exceptions import APIError
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class Banco:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        # CORREÇÃO: Chamar sup.get_key()
        self.client: Client = create_client(sup.get_instancia(), sup.get_key())
#--------------------------------------------------------------------------------------------------------------------#
    def busca_id_por_numero(self, numero: str):
        try:
            #Seleciona id a partir do numero de telefone
            dados_busca = self.client.table('usr').select("id").eq('numero', numero).execute().data

            #Em caso de sucesso retorna o id 
            if dados_busca:
                logger.info(f"Usuário {numero} encontrado. ID: {dados_busca[0]['id']}")
                return dados_busca[0]['id']
        except Exception as e:
            logger.error(f"Erro na busca inicial no Supabase: {e}")

        #Em caso de falha cria um novo registro no subase
        logger.info(f"Usuário {numero} não encontrado. Tentando criar novo registro.")
        try:
            novo_registro = {'numero': numero,}
            response_insert = self.client.table('usr').insert(novo_registro).execute()
            
            #instancia o novo id para retornalo
            novo_id = response_insert.data[0]['id']
            logger.info(f"Novo usuário {numero} criado com sucesso. ID: {novo_id}")
            return novo_id
        except APIError as e:
            logger.error(f"Erro ao inserir novo usuário (pode ser chave duplicada): {e}")
            return None
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado na inserção: {e}")
            return None
#--------------------------------------------------------------------------------------------------------------------#    
    def get_messages(self, user_id: int):
        try: 
            #Instancia a tabela de mensagens, usando id para filtrar 
            #e limitando a 5 ultimas mensagens(pega por timestamp decrescente)
            cnxt_data = (self.client
                         .table('mensagens_salvas')
                         .select('role, msg') 
                         .eq('usr_id', user_id)
                         .order('created_at', desc=True) 
                         .limit(5) 
                         .execute()).data
            #Inverte a ordem para ficar do mais antigo para o mais novo
            cnxt_data.reverse()
            
            #formata as mensagens e salva em uma lista para ficar no formato de janela de contexto
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