import re

def clean_ai_response(response: str) -> str:
    """
    Remove tags <think></think> e conteúdo entre elas das respostas da IA
    """
    # Remove os blocos <thinking>...</thinking>
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    
    # Remove possíveis espaços em branco extras resultantes
    response = response.strip()
    
    return response