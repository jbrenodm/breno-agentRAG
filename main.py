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

def format_output(results, questions):
    output_data = []
    
    for question, result in zip(questions, results):
        # Determina indentação baseada no tipo
        if question['type'] == 'subitem':
            indent = "    "
            display_text = f"{indent}{question['text']}"
        else:
            indent = ""
            display_text = question['text']
        
        output_data.append({
            'Ordem': question['original_order'] + 1,
            'Tipo': question['type'],
            'Pergunta': display_text,
            'Contexto': question.get('context', ''),
            'Resposta': result.get('resposta', 'N/A'),
            'Fonte': result.get('fontes', 'N/A'),
            'Trecho': result.get('trechos', 'N/A'),
            'Página': result.get('paginas', 'N/A')
        })
    
    return pd.DataFrame(output_data)


def main():
    parser = argparse.ArgumentParser(description='Processador RAG')
    parser.add_argument('input_file', help='Arquivo de entrada (XLSX, CSV, TXT)')
    parser.add_argument('output_file', help='Arquivo de saída (XLSX)')
    parser.add_argument('--workers', type=int, default=3, 
                      help='Número de workers paralelos (default: 3)')
    args = parser.parse_args()

    # Validação do arquivo de entrada
    if not os.path.exists(args.input_file):
        logger.error(f"Arquivo de entrada não encontrado: {args.input_file}")
        return

    # Carrega perguntas com metadados de hierarquia
    logger.info("Carregando perguntas...")
    questions = load_questions(args.input_file)
    
    if not questions:
        logger.error("Nenhuma pergunta válida encontrada")
        return

    # Processa mantendo a hierarquia
    results = process_in_parallel(
        questions,  # Agora é lista de dicionários com contexto
        query_rag,
        max_workers=args.workers,
        desc="Gerando respostas"
    )
    
     # Formata a saída mantendo hierarquia
    output_df = format_output(results, questions)
    output_df.to_excel(args.output_file, index=False)

if __name__ == "__main__":
    start_time = time.time()
    main()
    logger.info(f"Tempo total: {time.time() - start_time:.2f} segundos")