from typing import Dict, List, TypedDict

class RAGResponse(TypedDict):
    pergunta: str
    resposta: str
    fontes: str
    paginas: str
    trechos: str
    modelo: str
    tempo_resposta: str
    timestamp: int
    versao: str

class ErrorResponse(TypedDict):
    pergunta: str
    resposta: str
    fontes: str
    paginas: str
    trechos: str
    modelo: str
    tempo_resposta: str
    timestamp: int
    versao: str