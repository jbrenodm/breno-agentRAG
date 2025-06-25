import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"

def main():
    # Configuração do parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Resetar o banco de dados")
    args = parser.parse_args()

    if args.reset:
        clear_database()

    # Processamento dos documentos
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)

def load_documents():
    print(f"📂 Carregando documentos de {DATA_PATH}")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    return loader.load()

def split_documents(documents: list[Document]):
    print("✂️ Dividindo documentos em chunks")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    # Inicializa o Chroma (persistência é automática)
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    # Processamento em lotes menores
    batch_size = 500  # Reduzido para evitar sobrecarga
    print(f"📤 Adicionando {len(chunks)} documentos em lotes de {batch_size}")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_ids = [f"doc_{i+j}" for j, _ in enumerate(batch)]
        
        print(f"  Lote {i//batch_size + 1}: {len(batch)} documentos")
        db.add_documents(batch, ids=batch_ids)

    print("✅ Banco de dados atualizado")

def clear_database():
    if os.path.exists(CHROMA_PATH):
        print("🧹 Limpando banco de dados existente")
        shutil.rmtree(CHROMA_PATH)

if __name__ == "__main__":
    main()