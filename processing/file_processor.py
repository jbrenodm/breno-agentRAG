import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)

def load_questions(file_path: str) -> List[str]:
    """Carrega perguntas de arquivos"""
    try:
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, header=None)
            # print(f"DEBUG - Primeiras linhas:\n{df.head()}")  # Adicione esta linha para depuração
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None, encoding='utf-8')
        else:
            raise ValueError("Formato não suportado")
            
        return df[0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Erro ao carregar perguntas: {str(e)}")
        return []