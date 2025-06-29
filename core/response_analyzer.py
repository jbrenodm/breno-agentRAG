import re
from typing import Dict, Any
import logging
import json
from core.config import Settings  # Adicione esta importação


logger = logging.getLogger(__name__)

class ResponseAnalyzer:
    _ollama = None  # Instância compartilhada do Ollama

    @classmethod
    def initialize(cls):
        """Inicializa o cliente Ollama uma única vez"""
        if cls._ollama is None:
            settings = Settings()
            try:
                from langchain_ollama import Ollama
            except ImportError:
                from langchain_community.llms import Ollama
                logger.warning("Usando versão alternativa do Ollama")
            
            cls._ollama = Ollama(
                model=settings.model_name,
                temperature=0.3,  # Mais determinístico para análise
                num_ctx=4096
            )

    @staticmethod
    def evaluate_response(pergunta: str, resposta: str) -> Dict[str, Any]:
        """Análise baseada em regras (rápida)"""
        positive_keywords = [r"\bsim\b", r"\batende\b", r"\bimplementa\b"]
        negative_keywords = [r"\bnão\b", r"\bnão atende\b", r"\bfalta\b"]
        
        resposta_lower = resposta.lower()
        positive_count = sum(1 for k in positive_keywords if re.search(k, resposta_lower))
        negative_count = sum(1 for k in negative_keywords if re.search(k, resposta_lower))
        
        return {
            "atende": "SIM" if positive_count > negative_count else "NÃO",
            "correspondencia": f"{positive_count}/{negative_count}"
        }
    
    @classmethod
    def deep_analysis(cls, pergunta: str, resposta: str) -> Dict[str, str]:
        """
        Usa LLM para avaliar se a resposta tecnicamente atende à pergunta.
        Retorna: {"atende": "SIM/NÃO", "justificativa": str}
        """
        try:
            # Garante que o Ollama está inicializado
            if cls._ollama is None:
                cls.initialize()

            prompt = f"""
            ANALISE CRÍTICA TÉCNICA:
            - PERGUNTA: {pergunta}
            - RESPOSTA: {resposta}

            A resposta demonstra CLARAMENTE que o requisito técnico da pergunta é atendido pela solução?
            Considere:
            1. Respostas que confirmam explicitamente = "SIM"
            2. Respostas vagas ou que exigem configuração adicional = "NÃO"
            
            Responda APENAS com JSON válido: {{"atende": "SIM" ou "NÃO", "justificativa": "string"}}
            """
            
            # Chamada ao Ollama com timeout
            response = cls._ollama.generate(
                [prompt],
                stop=["\n"],  # Para evitar texto adicional
                timeout=30  # Timeout em segundos
            )
            
            # Extrai o JSON da resposta
            json_str = response.generations[0][0].text.strip()
            result = json.loads(json_str)
            
            # Valida a estrutura
            if not all(key in result for key in ["atende", "justificativa"]):
                raise ValueError("Resposta da IA incompleta")
                
            return result
            
        except json.JSONDecodeError:
            logger.error("Falha ao decodificar JSON da IA")
            return {"atende": "NÃO", "justificativa": "Erro na análise técnica"}
        except Exception as e:
            logger.error(f"Erro na análise profunda: {str(e)}")
            return {"atende": "NÃO", "justificativa": f"Falha na avaliação: {str(e)}"}