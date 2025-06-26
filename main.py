import argparse
import logging
import time
import os
import pandas as pd
from core.rag_service import query_rag
from processing.file_processor import load_questions
from processing.parallel import process_in_parallel
from core.utils import clean_ai_response


# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Processador RAG')
    parser.add_argument('input_file', help='Arquivo de entrada (XLSX, CSV)')
    parser.add_argument('output_file', help='Arquivo de saída (XLSX)')
    parser.add_argument('--workers', type=int, default=3, help='Número de workers paralelos')
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        logger.error(f"Arquivo de entrada não encontrado: {args.input_file}")
        return

    logger.info("Carregando perguntas...")
    questions = load_questions(args.input_file)
    
    if not questions:
        logger.error("Nenhuma pergunta válida encontrada")
        return

    logger.info(f"Processando {len(questions)} perguntas...")
    results = process_in_parallel(
        questions,
        query_rag,
        max_workers=args.workers,
        desc="Gerando respostas"
    )
    
    pd.DataFrame(results).to_excel(args.output_file, index=False)
    logger.info(f"Resultados salvos em {args.output_file}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    logger.info(f"Tempo total: {time.time() - start_time:.2f} segundos")