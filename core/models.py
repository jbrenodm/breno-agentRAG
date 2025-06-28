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
    contexto_hierarquico: str  # Novo campo

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
    contexto_hierarquico: str  # Novo campo

# Tipo unificado para retorno
RAGResult = Union[RAGResponse, ErrorResponse]