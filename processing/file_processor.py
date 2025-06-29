import pandas as pd
import logging
from typing import List
import re

logger = logging.getLogger(__name__)

def load_questions(file_path: str) -> List[dict]:
    """Carrega perguntas com metadados de hierarquia"""
    try:
        # Inicialização de contadores
        item_count = 0
        subitem_count = 0
        current_main_item = None
        current_main_text = None
        
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
        
        for idx, row in df.iterrows():
            text = str(row[0]).strip()
            
            # Item principal (prefixo •)
            if text.startswith('•'):
                item_count += 1
                subitem_count = 0
                current_main_item = f"Requisito {item_count}"
                current_main_text = text
                questions.append({
                    'text': text,
                    'type': 'main',
                    'numero': current_main_item,
                    'contexto': None,
                    'original_order': idx
                })
            
            # Subitem (prefixo o)
            elif text.startswith('o'):
                if current_main_item:  # Só adiciona se houver item principal
                    subitem_count += 1
                    questions.append({
                        'text': text,
                        'type': 'subitem',
                        'numero': f"{current_main_item}.{subitem_count}",
                        'contexto': current_main_text,  # Texto completo do item principal
                        'original_order': idx
                    })
                else:
                    logger.warning(f"Subitem sem item principal: {text}")
                    questions.append({
                        'text': text,
                        'type': 'standalone',
                        'contexto': None,
                        'original_order': idx
                    })
            
            # Item standalone
            else:
                current_main_item = None
                current_main_text = None
                questions.append({
                    'text': text,
                    'type': 'standalone',
                    'contexto': None,
                    'original_order': idx
                })
                
        return questions
    
    except Exception as e:
        logger.error(f"Erro ao carregar perguntas: {str(e)}")
        return []

def detect_hierarchy_level(text: str) -> int:
    """Detecta nível de hierarquia baseado em indentação ou prefixos"""
    # Remove espaços iniciais para análise
    clean_text = text.lstrip()
    
    # Baseado em prefixos
    if clean_text.startswith('•'):
        return 0  # Item principal
    elif clean_text.startswith('o'):
        return 1  # Subitem
    
    # Baseado em indentação
    indent_level = (len(text) - len(clean_text)) // 4  # Considera 4 espaços por nível
    if indent_level > 0:
        return indent_level
    
    # Baseado em numeração (1.1, 1.2.3, etc)
    match = re.match(r'^(\d+\.)+\d+', clean_text)
    if match:
        return match.group(0).count('.')
    
    return 0  # Item principal