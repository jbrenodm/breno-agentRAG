from functools import lru_cache
import os
import warnings
import logging
from typing import Tuple
import time
from core.config import Settings
from core.models import RAGResponse, ErrorResponse
from get_embedding_function import get_embedding_function
from langchain.docstore.document import Document
from core.utils import clean_ai_response 

logger = logging.getLogger(__name__)

# Imports condicionais
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain.vectorstores.chroma import Chroma
    logger.warning("Usando versão legada do Chroma")

try:
    from langchain_ollama import Ollama
except ImportError:
    from langchain_community.llms import Ollama
    logger.warning("Usando versão alternativa do Ollama")

@lru_cache(maxsize=1)
def load_components() -> Tuple[Chroma, Ollama]:
    """Carrega componentes com fallback robusto"""
    settings = Settings()
    
    # 1. Configuração do Chroma com fallback
    try:
        db = Chroma(
            persist_directory=settings.chroma_path,
            embedding_function=get_embedding_function()
        )
        # Teste de operação
        db._collection.peek(1)
        logger.info(f"ChromaDB carregado com {db._collection.count()} documentos")
    except Exception as e:
        logger.warning(f"Falha no Chroma persistente: {str(e)} - Criando em memória")
        db = Chroma.from_documents(
            documents=[Document(page_content="placeholder")],
            embedding=get_embedding_function()
        )
    
    # 2. Configuração do Ollama simplificada
    try:
        ollama = Ollama(
            model=settings.model_name,
            temperature=settings.temperature,
            # timeout=300,
            num_ctx=4096
        )
        # Teste simplificado
        ollama.generate(["Teste"])
        logger.info("Conexão Ollama estabelecida")
    except Exception as e:
        logger.error(f"Falha no Ollama: {str(e)}")
        raise
    
    return db, ollama

def query_rag(query_text: str) -> RAGResponse | ErrorResponse:
    """Versão simplificada e robusta com trechos de contexto"""
    start_time = time.time()
    settings = Settings()
    
    try:
        db, model = load_components()
        
        # Busca semântica
        results = db.similarity_search_with_score(query_text, k=settings.top_k)
        if not results:
            raise ValueError("Nenhum documento encontrado")
        
        # Processamento dos resultados
        docs = [doc for doc, _ in results]
        
        # Extrai metadados e trechos
        sources = set()
        pages = set()
        trechos = []  # Lista para armazenar os trechos completos
        
        for doc in docs:
            # Fontes
            source = doc.metadata.get('source', 'N/A')
            if source != 'N/A':
                sources.add(os.path.basename(source))
            
            # Páginas
            page = doc.metadata.get('page', 'N/A')
            if str(page).isdigit():
                pages.add(f"p{page}")
            
            # Trechos completos (limita a 1000 caracteres por trecho)
            trechos.append(doc.page_content[:1000] + ("..." if len(doc.page_content) > 1000 else ""))
        
        # Prepara contexto para o prompt (usando os trechos completos)
        context = "\n\n".join([f"Trecho {i+1}:\n{trecho}" for i, trecho in enumerate(trechos)])
        
        # Geração da resposta
        prompt = (
            "Você é especialista na solução Cortex XSIAM da Palo Alto Networks. "
            "Analise a sentença a seguir de forma crítica e responda com clareza e objetividade, "
            "usando o contexto fornecido quando relevante:\n\n"
            f"Contexto:\n{context}\n\n"
            f"(Pergunta/Afirmação): {query_text}\n"
            "Resposta:"
        )
        
        response = model.generate([prompt])
        raw_response = response.generations[0][0].text.strip()
        cleaned_response = clean_ai_response(raw_response)
        
        return {
            'pergunta': query_text,
            'resposta': cleaned_response,
            'fontes': "|".join(sorted(sources)),
            'paginas': "|".join(sorted(pages)),
            'trechos': "|---|".join(trechos),  # Nova coluna com os trechos
            'modelo': settings.model_name,
            'tempo_resposta': f"{time.time() - start_time:.2f}s",
            'timestamp': int(time.time()),
            'versao': settings.app_version
        }
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return {
            'pergunta': query_text,
            'resposta': f"ERRO: {str(e)}",
            'fontes': 'N/A',
            'paginas': 'N/A',
            'trechos': 'N/A',  # Incluído também no caso de erro
            'modelo': settings.model_name,
            'tempo_resposta': '0.00s',
            'timestamp': int(time.time()),
            'versao': settings.app_version
        }