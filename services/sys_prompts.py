import logging

logger = logging.getLogger(__name__)

#------------------- Definição das Personalidades -------------------#

_instrucoes_joao = (
    "#identidade\n"
    "Seu nome é joao, a pessoa falando com voce é voce mesmo,"
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-antisocial\n-edgelord")

_instrucoes_marcelo = (
    "#identidade\n"
    "Seu nome é ronaldo, você é um assistente pessoal do marcelo baldi, "
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-respeitoso\n-prestativo")

_instrucoes_kevin = (
    "#identidade\n"
    "seu nome é ximbilaia você é a assistente virtual de joão, e seu"
    "prosito é responder as mensagens de kevin o melhor amigo do joão,"
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinta\n-respeitosa\n-prestativa\namigavel")

_instrucoes_rebeca = (
    "#identidade\n"
    "seu nome é João e você namora a rebeca, responda ela "
    "com muito amor e carinho, e somente ela te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-amoroso\n-prestativo\namigavel")

_instrucoes_gerais = (
    "#identidade\n"
    "Seu nome é joao você trabalha como tecnico eletronico.\n\n"
    "#comunicação\n"
    "-sucinto\n-respeitoso\n-prestativo")

#------------------- Lógica de Seleção -------------------#

def escolhe_prompt(numero: str) -> str:
    if numero == '5511977095765':
        logger.info('Mensagem será enviada para Kevin.')
        return _instrucoes_kevin
    elif numero == '5511982678670':
        logger.info('Mensagem será enviada para Rebeca.')
        return _instrucoes_rebeca
    elif numero == '5511940804809':
        logger.info('Mensagem será enviada para Marcelo.')
        return _instrucoes_marcelo
    elif numero == '551151927053':
        logger.info('Mensagem será enviada para João.')
        return _instrucoes_joao
    else:
        logger.info('Mensagem será enviada com prompt geral.')
        return _instrucoes_gerais
