"""
tokens.py
=========

Estrutura de dados para os tokens processados pelo analisador léxico.
Compatível com Python 3.8+.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from .token_types import PALAVRAS_RESERVADAS, TokenType

AtributoToken = Optional[Union[int, float, str]]


@dataclass
class Token:
    """
    Representa uma unidade léxica (Token) extraída do código-fonte.
    """
    tipo: TokenType                    # Categoria do token (ex: IDENTIFICADOR, INTEIRO)
    lexema: str                      # Cadeia de texto exata lida do código
    linha: int                       # Linha do arquivo onde o token foi encontrado
    coluna: int                      # Coluna inicial do token na linha
    atributo: AtributoToken = None    # Valor avaliado (ex: 10 para um inteiro, valor da string

    @property
    def type(self) -> TokenType:
        return self.tipo

    @type.setter
    def type(self, value: TokenType) -> None:
        self.tipo = value

    @property
    def line(self) -> int:
        return self.linha

    @line.setter
    def line(self, value: int) -> None:
        self.linha = value

    @property
    def column(self) -> int:
        return self.coluna

    @column.setter
    def column(self, value: int) -> None:
        self.coluna = value

    @property
    def lexeme(self) -> str:
        return self.lexema

    @lexeme.setter
    def lexeme(self, value: str) -> None:
        self.lexema = value

    def display_type_name(self) -> str:
        """Retorna o nome externo esperado pelos fixtures."""
        mapping = {
            "KW_BOOL": "BOOL",
            "KW_INT": "INT",
            "KW_FLOAT": "FLOAT",
            "KW_CHAR": "CHAR",
            "KW_DOUBLE": "DOUBLE",
            "KW_VOID": "VOID",
            "KW_TRUE": "TRUE",
            "KW_FALSE": "FALSE",
            "KW_IF": "IF",
            "KW_ELSE": "ELSE",
            "KW_WHILE": "WHILE",
            "KW_FOR": "FOR",
            "KW_RETURN": "RETURN",
            "KW_BREAK": "BREAK",
            "KW_CONTINUE": "CONTINUE",
            "KW_PRINT": "PRINT",
            "KW_READ": "READ",
            "ID": "IDENT",
            "NUM_INT": "INT_LIT",
            "NUM_FLOAT": "FLOAT_LIT",
            "STRING": "STRING_LIT",
            "CHAR_LITERAL": "CHAR_LIT",
            "SEMI": "SEMICOLON",
        }
        return mapping.get(self.tipo.name, self.tipo.name)

    def obter_nome_exibicao(self) -> str:
        """Retorna o nome externo usado na tabela e no JSONL."""
        return self.display_type_name()

    @property
    def eh_palavra_reservada(self) -> bool:
        """Verifica se o token atual é uma palavra reservada da linguagem."""
        return self.tipo in PALAVRAS_RESERVADAS.values()

    def para_linha_tabela(self) -> tuple:
        """Formata o token para exibição em tabelas no terminal ou GUI."""
        texto_atributo = "" if self.atributo is None else str(self.atributo)
        return (self.obter_nome_exibicao(), self.lexema, self.linha, self.coluna, texto_atributo)

    def para_dicionario(self) -> dict:
        """Serializa o token para um dicionário estruturado."""
        return {
            "token": self.obter_nome_exibicao(),
            "lexeme": self.lexema,
            "attribute": self.atributo,
            "line": self.linha,
            "column": self.coluna,
        }

    def __str__(self) -> str:
        nome, lexema, linha, coluna, attr = self.para_linha_tabela()
        return f"{nome:<14} lexema={lexema!r:<16} lin={linha:<4} col={coluna:<4} attr={attr}"
