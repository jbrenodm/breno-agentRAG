try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain.vectorstores.chroma import Chroma
    print("⚠️ Usando versão legada do Chroma. Instale 'langchain-chroma' para melhor performance.")

try:
    from langchain_ollama import Ollama
except ImportError:
    from langchain_community.llms import Ollama
    print("⚠️ Usando versão alternativa do Ollama")

from get_embedding_function import get_embedding_function
from functools import lru_cache
from typing import Dict
import time
import warnings

# Configurações
CHROMA_PATH = "chroma"
MODEL_NAME = "deepseek-r1:8b"
TEMPERATURE = 0.3

@lru_cache(maxsize=1)
def load_components() -> tuple:
    """Versão ultra-compatível sem parâmetros problemáticos"""
    warnings.filterwarnings("ignore", category=UserWarning)
    
    return (
        Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=get_embedding_function()
        ),
        Ollama(
            model=MODEL_NAME,
            temperature=TEMPERATURE
        )
    )

def query_rag(query_text: str) -> Dict[str, str]:
    """Processamento RAG com tratamento robusto de erros"""
    try:
        db, model = load_components()
        
        # 1. Busca semântica
        results = db.similarity_search_with_score(query_text, k=2)
        
        # 2. Geração da resposta
        context = "\n".join([doc.page_content for doc, _ in results])
        prompt = f"Responda baseado no contexto:\n{context}\n\nAnalise a sentença a seguir a respeito dos dashboards e relatórios do Cortex XSIAM.{query_text}\nResposta:"
        
        response_text = model.generate([prompt]).generations[0][0].text.strip()
        
        return {
            'pergunta': query_text,
            'resposta': response_text,
            'fontes': "|".join(sorted({doc.metadata.get('source', 'N/A') for doc, _ in results})),
            'paginas': "|".join(sorted({str(doc.metadata.get('page', 'N/A')) for doc, _ in results}))
        }
        
    except Exception as e:
        return {
            'pergunta': query_text,
            'resposta': f"ERRO: {str(e)}",
            'fontes': 'N/A',
            'paginas': 'N/A'
        }