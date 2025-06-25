import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Dict
from query_data_fast import query_rag
import argparse
import warnings
from datetime import datetime


# Configurações de performance para RTX 2050 Mobile
MAX_WORKERS = 3  # Número seguro para notebooks
CHUNK_SIZE = 8   # Processamento em lotes
GPU_MONITOR = True  # Habilita monitoramento de recursos

def setup_gpu_monitoring():
    """Configura monitoramento opcional da GPU"""
    try:
        import torch
        return {
            'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU',
            'func': lambda: f"{torch.cuda.memory_allocated()/1024**2:.1f}MB"
        }
    except ImportError:
        return {'device': 'N/A', 'func': lambda: 'N/A'}

def load_requirements(file_path: str) -> List[str]:
    """Carrega perguntas de arquivos com tratamento robusto"""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return pd.read_csv(file_path, usecols=[0], header=None, encoding='utf-8')[0].dropna().tolist()
        elif ext in ('.xlsx', '.xls'):
            return pd.read_excel(file_path, usecols=[0], header=None)[0].dropna().tolist()
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        else:
            raise ValueError(f"Formato não suportado: {ext}")
    except Exception as e:
        print(f"🚨 Erro ao carregar arquivo: {str(e)}")
        return []

def process_chunk(chunk: List[str], gpu_info: Dict) -> List[Dict]:
    """Processa um lote de perguntas"""
    chunk_results = []
    for question in chunk:
        try:
            result = query_rag(question)
            result.update({
                'GPU': gpu_info['device'],
                'VRAM': gpu_info['func'](),
                'Hora': datetime.now().strftime("%H:%M:%S")
            })
            chunk_results.append(result)
        except Exception as e:
            chunk_results.append({
                'pergunta': question,
                'resposta': f"ERRO: {str(e)}",
                'fontes': 'N/A',
                'paginas': 'N/A',
                'timestamp': time.time(),
                'GPU': gpu_info['device'],
                'VRAM': 'N/A',
                'Hora': datetime.now().strftime("%H:%M:%S")
            })
    return chunk_results

def save_backup(results: List[Dict], output_file: str):
    """Salva resultados parciais"""
    temp_file = f"temp_{output_file}"
    pd.DataFrame(results).to_csv(temp_file, index=False, sep=';', encoding='utf-8-sig')

def main():
    warnings.filterwarnings('ignore')
    
    # Configuração do parser de argumentos
    parser = argparse.ArgumentParser(description='Processador RAG de alta performance')
    parser.add_argument('input_file', help='Arquivo de entrada (.csv, .xlsx, .txt)')
    parser.add_argument('output_file', help='Arquivo de saída (.csv)')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'Número de workers (padrão: {MAX_WORKERS})')
    args = parser.parse_args()

    # Verificação inicial
    if not os.path.exists(args.input_file):
        print(f"❌ Arquivo não encontrado: {args.input_file}")
        return

    print("\n⚡ Iniciando processamento RAG otimizado")
    print(f"🔧 Configuração: {args.workers} workers | Chunks de {CHUNK_SIZE} perguntas")
    
    # Monitoramento de hardware
    gpu_info = setup_gpu_monitoring() if GPU_MONITOR else {'device': 'N/A', 'func': lambda: 'N/A'}
    print(f"🖥️  Dispositivo: {gpu_info['device']}")

    # Carregamento das perguntas
    questions = load_requirements(args.input_file)
    if not questions:
        print("❌ Nenhuma pergunta válida encontrada")
        return

    print(f"📊 Total de perguntas: {len(questions)}")
    print("⏳ Processando... (Ctrl+C para pausar)")

    # Processamento paralelo em chunks
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = []
            chunks = [questions[i:i + CHUNK_SIZE] for i in range(0, len(questions), CHUNK_SIZE)]
            
            for chunk in chunks:
                futures.append(executor.submit(process_chunk, chunk, gpu_info))
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Progresso"):
                results.extend(future.result())
                save_backup(results, args.output_file)  # Backup incremental

    except KeyboardInterrupt:
        print("\n⚠️ Interrupção recebida - salvando resultados parciais...")
    
    # Pós-processamento
    df = pd.DataFrame(results)
    
    # Reorganiza colunas
    final_columns = [
        'pergunta', 'resposta', 'fontes', 'paginas',
        'GPU', 'VRAM', 'Hora', 'timestamp'
    ]
    df = df[[col for col in final_columns if col in df.columns]]
    
    # Salva resultados
    df.to_csv(args.output_file, index=False, sep=';', encoding='utf-8-sig')
    
    # Estatísticas finais
    success_rate = (df['resposta'].str.contains('ERRO') == False).mean()
    print(f"\n✅ Processamento concluído - {len(df)} respostas")
    print(f"📈 Taxa de sucesso: {success_rate:.1%}")
    print(f"💾 Resultados salvos em: {args.output_file}")
    print(f"🕒 Última atualização: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print(f"⏱️ Tempo total: {time.time() - start_time:.2f} segundos")