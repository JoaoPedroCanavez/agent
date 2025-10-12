import logging
from openai import OpenAI
from typing import List, Dict
import re

logger = logging.getLogger(__name__)

class Agente:

  def __init__(self, key: str):
    self.client =  OpenAI(api_key=key)

  def processar_input(self, usr_text: str, instrucoes: str, contexto: List[Dict]) -> str:
        
        logger.info(f"Input do Usuário para o Agente: '{usr_text}'")
        try:
            # 1. VERIFICA SE O INPUT É UM COMANDO DE VISION/MÍDIA
            # Busca o padrão de URL e instrução injetado pelo processador_midia.py
            match = re.search(r'IMAGEM RECEBIDA \(URL: (.*)\)\. TAREFA: (.*)', usr_text)
            
            # Inicializa a lista de mensagens
            messages = [{"role": "system", "content": instrucoes}]
            messages.extend(contexto)
            
            modelo_a_usar = "gpt-4o-mini" # Padrão para texto
            
            if match:
                media_url = match.group(1)
                instrucao_imagem = match.group(2)
                modelo_a_usar = "gpt-4o" # Usa modelo com Visão
                
                # Monta o objeto de mensagem de visão (multimodal)
                vision_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instrucao_imagem},
                        {"type": "image_url", "image_url": {"url": media_url}}
                    ]
                }
                messages.append(vision_message)
                logger.info("Chamada VISION formatada para GPT-4o.")

            else:
                # Se não for Vision, é texto simples ou transcrição/documento
                messages.append({"role": "user", "content": usr_text})
                
            # 2. CHAMA A API COM O MODELO E AS MENSAGENS CORRETAS
            response = self.client.chat.completions.create(
                model=modelo_a_usar, # Usa gpt-4o para Vision, gpt-4o-mini para texto/audio
                messages=messages,  
                temperature=0.5,
                max_tokens=2048,      
                top_p=1
            )
            
            resposta_do_agente = response.choices[0].message.content
            logger.info("Resposta da OpenAI recebida com sucesso.")
            return resposta_do_agente

        except Exception as e:
            logger.error(f"Erro ao chamar o Agente OpenAI: {e}", exc_info=True)
            return "Desculpe, Marcelo, tive um problema para processar sua solicitação agora. Por favor, tente novamente mais tarde."