import os
import argparse
import pandas as pd
from typing import List, Dict, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import time
import warnings
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backward compatible imports
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain.vectorstores.chroma import Chroma
    logger.warning("Using legacy Chroma version. Install 'langchain-chroma' for better performance.")

try:
    from langchain_ollama import Ollama
except ImportError:
    from langchain_community.llms import Ollama
    logger.warning("Using alternative Ollama implementation")

from get_embedding_function import get_embedding_function

class Settings(BaseSettings):
    chroma_path: str = "chroma"
    model_name: str = "deepseek-r1:8b"
    temperature: float = 0.3
    top_k: int = 2
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache(maxsize=1)
def load_components() -> Tuple[Chroma, Ollama]:
    """Load RAG components with caching"""
    warnings.filterwarnings("ignore", category=UserWarning)
    settings = Settings()
    logger.info(f"Loading components (v{settings.app_version})")
    
    return (
        Chroma(
            persist_directory=settings.chroma_path,
            embedding_function=get_embedding_function()
        ),
        Ollama(
            model=settings.model_name,
            temperature=settings.temperature,
            # timeout=120
        )
    )

def extract_metadata(results) -> Dict[str, str]:
    """Extract and format metadata from documents"""
    sources = set()
    pages = set()
    
    for doc, _ in results:
        source = doc.metadata.get('source', 'N/A')
        if source != 'N/A':
            sources.add(os.path.basename(source))
        page = doc.metadata.get('page', 'N/A')
        if str(page).isdigit():
            pages.add(f"p{page}")
            
    return {
        'fontes': "|".join(sorted(sources)) if sources else "N/A",
        'paginas': "|".join(sorted(pages)) if pages else "N/A"
    }

def validate_response(response: str) -> str:
    """Validate and sanitize model response"""
    response = response.strip()
    if not response or len(response) > 10000:
        raise ValueError("Invalid or too long response")
    return response

def query_rag(query_text: str) -> Dict[str, str]:
    """Process a single query through RAG pipeline"""
    start_time = time.time()
    settings = Settings()
    
    try:
        db, model = load_components()
        results = db.similarity_search_with_score(query_text, k=settings.top_k)
        
        if not results:
            logger.warning("No results found in semantic search")
            raise ValueError("No results found in semantic search")
        
        metadata = extract_metadata(results)
        context = "\n".join([doc.page_content for doc, _ in results])
        
        prompt = f"""Você é um assistente especializado na solução Cortex XSIAM da Palo Alto Networks.
        
Contexto:
{context}

Pergunta: {query_text}

Responda de forma clara e concisa, citando os números das páginas relevantes quando aplicável.
Resposta:"""
        
        response = model.generate([prompt]).generations[0][0].text
        validated_response = validate_response(response)
        
        response_time = time.time() - start_time
        
        return {
            'pergunta': query_text,
            'resposta': validated_response,
            'fontes': metadata['fontes'],
            'paginas': metadata['paginas'],
            'modelo': settings.model_name,
            'tempo_resposta': f"{response_time:.2f}s",
            'timestamp': int(time.time()),
            'versao': settings.app_version
        }
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Error processing query: {str(e)}")
        return {
            'pergunta': query_text,
            'resposta': f"ERRO ({error_type}): {str(e)}",
            'fontes': 'N/A',
            'paginas': 'N/A',
            'modelo': settings.model_name,
            'tempo_resposta': f"{(time.time() - start_time):.2f}s",
            'timestamp': int(time.time()),
            'versao': settings.app_version
        }

def load_questions(file_path: str) -> List[str]:
    """Load questions from input file"""
    try:
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, header=None)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None, encoding='utf-8')
        else:
            raise ValueError("Unsupported file format")
            
        return df[0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Process questions through RAG pipeline')
    parser.add_argument('input_file', help='Input file (XLSX, CSV)')
    parser.add_argument('output_file', help='Output file (XLSX)')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers')
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        return

    questions = load_questions(args.input_file)
    if not questions:
        logger.error("No valid questions found in input file")
        return

    logger.info(f"Processing {len(questions)} questions...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(query_rag, q) for q in questions]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            results.append(future.result())

    # Save results
    pd.DataFrame(results).to_excel(args.output_file, index=False)
    logger.info(f"Results saved to {args.output_file}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")