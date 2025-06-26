from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Callable, Any

def process_in_parallel(
    tasks: List[Any],
    processing_func: Callable,
    max_workers: int = 5,
    desc: str = "Processando"
) -> List[Any]:
    """Executa processamento paralelo com barra de progresso"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(processing_func, task) for task in tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc):
            results.append(future.result())
    return results