# evolution.py

import json
import requests
from dotenv import load_dotenv

class EvoConnection:
    def __init__(self, evoURL, evoIns, evoToken, agente_instancia):
        self.EVO_URL = evoURL
        self.EVO_INSTANCIA = evoIns
        self.EVO_TOKEN = evoToken
        self.agente = agente_instancia

    async def processar_webhook(self, data: dict):
        if 'messages' not in data or not data['messages']:
            return {"status": "ok", "message": "Nenhuma mensagem encontrada para processamento."}
        
        for message in data['messages']:
            
            if message.get('key', {}).get('fromMe', False):
                continue
            
            # 1. Tenta extrair o texto de diferentes campos
            usr_text = message.get('message', {}).get('conversation') or \
                        message.get('message', {}).get('extendedTextMessage', {}).get('text')
            
            numero = message.get('key', {}).get('remoteJid', '')       
            f_numero = numero.split('@')[0]
            
            # ---------------------------------------------------------------
            # 💡 NOVO DEBUG: Vê se o texto foi extraído antes de chamar a IA
            print(f"\n--- DEBUG INÍCIO PROCESSAMENTO ---")
            print(f"DEBUG: Mensagem recebida de: {f_numero}")
            print(f"DEBUG: Texto extraído: '{usr_text}'")
            # ---------------------------------------------------------------

            if usr_text: # Verifica se o texto não é vazio (ou None)
                
                # SE VOCÊ CHEGAR AQUI, A IA SERÁ CHAMADA!
                print("DEBUG: Chamando o Agente OpenAI...")
                resposta_agente = self.agente.processar_input(usr_text)
                print("DEBUG: Agente OpenAI respondeu.")

                self.enviar_resposta(f_numero, resposta_agente)
            else:
                print("DEBUG: Texto vazio ou tipo de mensagem não suportado (ignorado).")
                
        return {"status": "ok", "message": "Mensagens processadas e respostas enviadas."}
    
    
    def enviar_resposta(self, numero: str, resposta: str):

        if not self.EVO_URL or not self.EVO_INSTANCIA or not self.EVO_TOKEN:
            print("Erro: URL, Instância ou Chave da Evolution não configuradas.")
            return False

        url = f"{self.EVO_URL}/message/sendText/{self.EVO_INSTANCIA}" 
        
        payload = json.dumps({
        "number": numero,
        "text": resposta
        })
        
        headers = {
        'Content-Type': 'application/json', 
        'apikey': self.EVO_TOKEN, 
        }
        
        
        print(f"DEBUG: Tentando enviar para URL: {url}")
        print(f"DEBUG: Payload de Envio: {payload}")
        print(f"DEBUG: Chave API: {self.EVO_TOKEN}")

        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status() 
            print(f"-> Resposta Evolution API enviada. Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar mensagem pela Evolution API: {e}")
            if response is not None:
                print(f"Detalhes do erro da Evolution: {response.text}")
            return False