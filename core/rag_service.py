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
from core.response_analyzer import ResponseAnalyzer
import json

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

def query_rag(query_input: str | dict) -> RAGResponse | ErrorResponse:
    """Versão que considera contexto hierárquico"""
    start_time = time.time()
    settings = Settings()
    
    try:
        # Determina se a entrada é um dicionário com contexto ou apenas texto
        if isinstance(query_input, dict):
            query_text = query_input['text']
            context = query_input.get('context', None)
        else:
            query_text = query_input
            context = None
        
        db, model = load_components()
        
        # Se houver contexto, usa ambos para a busca
        search_query = f"{context}\n{query_text}" if context else query_text
        
        # Busca semântica (agora usando search_query que pode incluir contexto)
        results = db.similarity_search_with_score(search_query, k=settings.top_k)
        if not results:
            raise ValueError("Nenhum documento encontrado")
        
        # Processamento dos resultados
        docs = [doc for doc, _ in results]
        
        # Extrai metadados e trechos
        sources = set()
        pages = set()
        trechos = []
        
        for doc in docs:
            # Fontes
            source = doc.metadata.get('source', 'N/A')
            if source != 'N/A':
                sources.add(os.path.basename(source))
            
            # Páginas
            page = doc.metadata.get('page', 'N/A')
            if str(page).isdigit():
                pages.add(f"p{page}")
            
            # Trechos completos
            trechos.append(doc.page_content[:1000] + ("..." if len(doc.page_content) > 1000 else ""))
        
        # Prepara contexto para o prompt
        retrieved_context = "\n\n".join([f"Trecho {i+1}:\n{trecho}" for i, trecho in enumerate(trechos)])
        
        # Geração da resposta - agora incluindo o contexto hierárquico se existir
        prompt_parts = [
            "Você é especialista na solução Cortex XSIAM da Palo Alto Networks.",
            "Analise o requisito a seguir de forma crítica e responda com clareza e objetividade.",
            "Inicie a resposta com 'SIM' ou 'NÃO', seguido de uma justificativa Concisa, técnica e curta.",
            ""
        ]
        
        if context:
            prompt_parts.append(f"Contexto Hierárquico:\n{context}")
        
        prompt_parts.extend([
            f"Contexto Recuperado:\n{retrieved_context}",
            "",
            f"Requisito específico: {query_text}",
            "Resposta:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        response = model.generate([full_prompt])
        raw_response = response.generations[0][0].text.strip()
        cleaned_response = clean_ai_response(raw_response)
       # Análise da resposta - versão simplificada e funcional
        analysis_result = ResponseAnalyzer.evaluate_response(query_text, cleaned_response)
        atende = analysis_result["atende"]
        
        return {
            'pergunta': query_text,
            'resposta': cleaned_response,
            'fontes': "|".join(sorted(sources)),
            'paginas': "|".join(sorted(pages)),
            'trechos': "|---|".join(trechos),
            'modelo': settings.model_name,
            'tempo_resposta': f"{time.time() - start_time:.2f}s",
            'timestamp': int(time.time()),
            'versao': settings.app_version,
            'contexto_hierarquico': context if context else 'N/A',
            'atende': analysis_result['atende']  # Usando o resultado direto da análise
        }
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return {
            'pergunta': query_text if 'query_text' in locals() else str(query_input),
            'resposta': f"ERRO: {str(e)}",
            'fontes': 'N/A',
            'paginas': 'N/A',
            'trechos': 'N/A',
            'modelo': settings.model_name,
            'tempo_resposta': '0.00s',
            'timestamp': int(time.time()),
            'versao': settings.app_version,
            'contexto_hierarquico': context if 'context' in locals() else 'N/A',
            'atende': 'NÃO'  # Em caso de erro, considera como não atendido
        }