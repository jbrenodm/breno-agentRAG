import re
from typing import List

class ResponseAnalyzer:
    POSITIVE_INDICATORS = [
        r"\bsim\b", r"\batende\b", r"\bpossui\b", r"\bcontém\b",
        r"\bimplementa\b", r"\bsuporta\b", r"\bdisponível\b",
        r"\bverdadeiro\b", r"\bpositivo\b", r"\bcorreto\b"
    ]
    
    NEGATIVE_INDICATORS = [
        r"\bnão\b", r"\bnão atende\b", r"\bfalta\b", r"\bausente\b",
        r"\bincompleto\b", r"\bnegativo\b", r"\berro\b", r"\bfalso\b"
    ]
    
    @classmethod
    def is_positive(cls, response: str) -> bool:
        """Analisa a resposta para determinar se é positiva"""
        response_lower = response.lower()
        
        # Conta os indicadores positivos e negativos
        positive_count = sum(
            1 for indicator in cls.POSITIVE_INDICATORS 
            if re.search(indicator, response_lower)
        )
        
        negative_count = sum(
            1 for indicator in cls.NEGATIVE_INDICATORS 
            if re.search(indicator, response_lower)
        )
        
        # Considera como positivo se houver mais indicadores positivos
        return positive_count > negative_count