import logging
from data.apis import sup
from supabase import create_client, Client
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

class Banco:
    def __init__(self):
        # CORREÇÃO: Chamar sup.get_key()
        self.client: Client = create_client(sup.get_instancia(), sup.get_key())

    def busca_id_por_numero(self, numero: str):
        # A lógica de busca e upsert está OK e foi mantida.
        try:
            dados_busca = (
                self.client
                .table('usr')
                .select("id")
                .eq('numero', numero)
                .execute()
            ).data

            if dados_busca:
                logger.info(f"Usuário {numero} encontrado. ID: {dados_busca[0]['id']}")
                return dados_busca[0]['id']

        except Exception as e:
            logger.error(f"Erro na busca inicial no Supabase: {e}")

        logger.info(f"Usuário {numero} não encontrado. Tentando criar novo registro.")
        try:
            novo_registro = {
                'numero': numero,
            }
            response_insert = (
                self.client
                .table('usr')
                .insert(novo_registro)
                .execute()
            )
            
            novo_id = response_insert.data[0]['id']
            logger.info(f"Novo usuário {numero} criado com sucesso. ID: {novo_id}")
            return novo_id

        except APIError as e:
            logger.error(f"Erro ao inserir novo usuário (pode ser chave duplicada): {e}")
            return None
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado na inserção: {e}")
            return None
        
    
    # CORREÇÃO PRINCIPAL: Simplificar a obtenção de contexto
    def get_messages(self, user_id: int):
        # 1. Obter todas as mensagens ordenadas pelo tempo de criação (created_at ou similar)
        try:
            # Assumindo que a tabela 'mensagens_salvas' tem uma coluna 'created_at' para ordenação.
            cnxt_data = (self.client
                         .table('mensagens_salvas')
                         .select('role, msg') # Projeta apenas as colunas necessárias
                         .eq('usr_id', user_id)
                         .order('created_at', desc=False) # ORDENAÇÃO CRONOLÓGICA É CRUCIAL
                         .limit(10) # Limita a janela de contexto para as últimas 10 mensagens
                         .execute()).data
            
            # 2. Formata para o JSON do OpenAI: {'role': '...', 'content': '...'}
            # Os dados do Supabase já vêm como lista de dicionários; precisamos renomear 'msg' para 'content'.
            contexto_formatado = []
            for item in cnxt_data:
                 contexto_formatado.append({
                     'role': item['role'],
                     'content': item['msg']
                 })
            
            return contexto_formatado
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto do Supabase para ID {user_id}: {e}", exc_info=True)
            return [] # Retorna lista vazia em caso de falha para não quebrar a IA
    
    # CORREÇÃO PRINCIPAL: Adicionar uma nova mensagem é uma INSERÇÃO, não uma atualização complexa.
    def adiciona_mensagem(self, user_id: int, role: str, mensagem: str):
        try:
            novo_registro_msg = {
                'usr_id': user_id,
                'role': role,
                'msg': mensagem
                # O created_at deve ser gerado automaticamente pelo Supabase
            }
            
            (self.client
             .table('mensagens_salvas')
             .insert(novo_registro_msg)
             .execute())
             
            logger.info(f"Mensagem de '{role}' salva com sucesso para ID {user_id}.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem no Supabase para ID {user_id}: {e}", exc_info=True)
            return False

    # Função 'separa_contexto' removida, pois sua lógica foi integrada a get_messages.