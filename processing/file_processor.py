import pandas as pd
import logging
from typing import List
import re

logger = logging.getLogger(__name__)

# Novo file_processor.py
def load_questions(file_path: str) -> List[dict]:
    """Carrega perguntas com metadados de hierarquia"""
    try:
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, header=None)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None, encoding='utf-8')
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            df = pd.DataFrame(lines)
        else:
            raise ValueError("Formato não suportado")
            
        questions = []
        current_context = None
        
        for idx, row in df.iterrows():
            text = str(row[0]).strip()
            
            # Identifica itens principais (começam com •)
            if text.startswith('•'):
                current_context = text
                questions.append({
                    'text': text,
                    'type': 'main',
                    'context': None,
                    'original_order': idx
                })
            # Identifica subitens (começam com o)
            elif text.startswith('o') and current_context:
                questions.append({
                    'text': text,
                    'type': 'subitem',
                    'context': current_context,
                    'original_order': idx
                })
            else:
                current_context = None
                questions.append({
                    'text': text,
                    'type': 'standalone',
                    'context': None,
                    'original_order': idx
                })
                
        return questions
    except Exception as e:
        logger.error(f"Erro ao carregar perguntas: {str(e)}")
        return []

def detect_hierarchy_level(text: str) -> int:
    """Detecta nível de hierarquia baseado em indentação ou prefixos"""
    # Implementação básica - pode ser personalizada
    if text.startswith(('    ', '\t')):
        return 1  # Subitem
    elif re.match(r'^\d+\.\d+', text):
        return text.count('.')  # Nível baseado em numeração (1.1, 1.1.1, etc)
    else:
        return 0  # Item principal