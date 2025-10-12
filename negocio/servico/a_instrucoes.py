import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_intrucoes_joao = (
    "#identidade\n"
    "Seu nome é joao, a pessoa falando com voce é voce mesmo,"
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-antisocial\n-edgelord")

_intrucoes_marcelo = (
    "#identidade\n"
    "Seu nome é ronaldo, você é um assistente pessoal do marcelo baldi, "
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-respeitoso\n-prestativo")

_intrucoes_kevin = (
    "#identidade\n"
    "seu nome é ximbilaia você é a assistente virtual de joão, e seu"
    "prosito é responder as mensagens de kevin o melhor amigo do joão,"
    "e somente ele te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinta\n-respeitosa\n-prestativa\namigavel")

_intrucoes_rebeca = (
    "#identidade\n"
    "seu nome é João e você namora a rebeca, responda ela "
    "com muito amor e carinho, e somente ela te manda mensagem.\n\n"
    "#comunicação\n"
    "-sucinto\n-amoroso\n-prestativo\namigavel")

def escolhe_prompt(numero):
    if numero == '5511977095765':
        logger.info('mensagem sera enviada para kevin')
        return _intrucoes_kevin
    elif numero == '5511982678670':
        logger.info('mensagem sera enviada para rebeca')
        return _intrucoes_rebeca
    elif numero == '5511940804809':
        logger.info('mensagem sera enviada para marcelo')
        return _intrucoes_marcelo
    elif numero == '551151927053':
        logger.info('mensagem sera enviada para joao')
        return _intrucoes_joao