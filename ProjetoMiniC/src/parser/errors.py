"""
errors.py (parser)
===================
Erro sintático levantado pelo analisador sintático (Parser) do MiniC.
Segue o mesmo padrão de diagnóstico do ErroLexico do analisador léxico
(linha, coluna, mensagem, lexema/token envolvido) para manter os
relatórios do compilador consistentes entre as etapas.
"""

from __future__ import annotations


class ErroSintatico(Exception):
    """Erro de análise sintática: token encontrado não é válido no contexto atual."""
    codigo: str = "ERRO_SINTATICO"

    def __init__(self, mensagem: str, linha: int, coluna: int,
                 encontrado: str = "", esperado: str = ""):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.encontrado = encontrado
        self.esperado = esperado
        super().__init__(self.diagnostico())

    def diagnostico(self) -> str:
        """Gera mensagem formatada no padrão: 'linha X, coluna Y: <mensagem>'."""
        origem = f"; encontrado {self.encontrado!r}" if self.encontrado else ""
        return f"linha {self.linha}, coluna {self.coluna}: {self.mensagem}{origem}"
