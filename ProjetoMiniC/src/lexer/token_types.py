"""
token_types.py
==============

Enumeração de tokens e mapa de palavras reservadas da linguagem MiniC.
"""

from enum import Enum, auto
from typing import Dict


class TokenType(Enum):
    # Palavras reservadas
    KW_BOOL = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_CHAR = auto()
    KW_DOUBLE = auto()
    KW_VOID = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_RETURN = auto()
    KW_BREAK = auto()
    KW_CONTINUE = auto()
    KW_PRINT = auto()
    KW_READ = auto()

    # Identificador e Literais
    ID = auto()
    NUM_INT = auto()
    NUM_FLOAT = auto()
    STRING = auto()
    CHAR_LITERAL = auto()

    # Operadores aritméticos
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    # Atribuição e relacionais
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()

    # Operadores lógicos
    AND = auto()   # &&
    OR = auto()    # ||
    NOT = auto()   # !
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    SEMI = auto()           # ;
    COMMA = auto()          # ,
    DOT = auto()            # .

    # Controle
    EOF = auto()
    ERROR = auto()

# Mapeamento estático para identificação rápida de palavras reservadas
PALAVRAS_RESERVADAS: Dict[str, TokenType] = {
    "bool": TokenType.KW_BOOL,
    "int": TokenType.KW_INT,
    "float": TokenType.KW_FLOAT,
    "char": TokenType.KW_CHAR,
    "double": TokenType.KW_DOUBLE,
    "void": TokenType.KW_VOID,
    "true": TokenType.KW_TRUE,
    "false": TokenType.KW_FALSE,
    "if": TokenType.KW_IF,
    "else": TokenType.KW_ELSE,
    "while": TokenType.KW_WHILE,
    "for": TokenType.KW_FOR,
    "return": TokenType.KW_RETURN,
    "break": TokenType.KW_BREAK,
    "continue": TokenType.KW_CONTINUE,
    "print": TokenType.KW_PRINT,
    "read": TokenType.KW_READ,
}
