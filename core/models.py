from typing import Dict, List, TypedDict, Union

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
    contexto_hierarquico: str
    atende: str
    correspondencia: str  # Novo campo
    positive_indicators: int  # Novo campo
    negative_indicators: int  # Novo campo

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
    contexto_hierarquico: str
    atende: str
    correspondencia: str  # Novo campo
    positive_indicators: int  # Novo campo
    negative_indicators: int  # Novo campo

RAGResult = Union[RAGResponse, ErrorResponse]