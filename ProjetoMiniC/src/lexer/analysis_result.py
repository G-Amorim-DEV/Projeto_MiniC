"""
analysis_result.py
==================
Estruturas de suporte para armazenamento do estado dos dados gerados após análise léxica.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .errors import ErroLexico
from .tokens import Token


@dataclass
class ResultadoAnalise:
    """Contêiner principal com o inventário completo de tokens e erros acumulados."""
    tokens: List[Token] = field(default_factory=list)
    erros: List[ErroLexico] = field(default_factory=list)

    @property
    def possui_erros(self) -> bool:
        """Informa se a análise encontrou falhas léxicas."""
        return len(self.erros) > 0


@dataclass
class VisaoAnalise:
    """Estrutura utilizada pelas interfaces visuais/CLI para exibição de relatórios."""
    titulo: str
    fonte: str
    resultado: ResultadoAnalise
    saida_formatada: str
    tokens_jsonl: str = ""
    erros_jsonl: str = ""
    caminho_fonte: Optional[Path] = None