import pandas as pd
import logging
from typing import List, Dict, Any  # Adicionei os imports faltantes
import re

logger = logging.getLogger(__name__)

def load_questions(file_path: str) -> List[Dict[str, Any]]:
    """Versão melhorada com:
    - Tratamento de linhas vazias
    - Hierarquia mais precisa
    - Metadados adicionais
    """
    try:
        item_count = subitem_count = 0
        current_main_item = current_main_text = None
        questions = []
        
        # Implementação real do carregamento (que estava faltando)
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
        
        for idx, row in df.iterrows():
            text = str(row[0]).strip()
            if not text:
                continue
                
            level = detect_hierarchy_level(text)
            
            if level == 0 or text.startswith('•'):
                item_count += 1
                subitem_count = 0
                current_main_item = f"R{item_count}"
                current_main_text = text
                questions.append({
                    'text': text,
                    'type': 'main',
                    'numero': current_main_item,
                    'contexto': None,
                    'level': 0,
                    'original_order': idx
                })
            
            elif level >= 1 or text.startswith('o'):
                subitem_count += 1
                parent = current_main_item if current_main_item else f"UNK{idx}"  # Mudei ORPHAN para UNK
                questions.append({
                    'text': text,
                    'type': 'subitem',
                    'numero': f"{parent}.{subitem_count}",
                    'contexto': current_main_text,
                    'level': level,
                    'original_order': idx
                })
            
            else:
                questions.append({
                    'text': text,
                    'type': 'standalone',
                    'numero': f"S{idx+1}",
                    'contexto': None,
                    'level': level,
                    'original_order': idx
                })
                
        return questions
    
    except Exception as e:
        logger.error(f"Erro ao carregar: {str(e)}", exc_info=True)
        return []

def detect_hierarchy_level(text: str) -> int:
    """Versão corrigida com retorno garantido de int"""
    clean_text = text.lstrip()
    
    if clean_text.startswith('•'):
        return 0
    elif clean_text.startswith('o'):
        return 1
    
    indent_level = (len(text) - len(clean_text)) // 4
    if indent_level > 0:
        return indent_level
    
    match = re.match(r'^(\d+\.)+\d+', clean_text)
    if match:
        return match.group(0).count('.')
    
    return 0  # Garante sempre retornar int