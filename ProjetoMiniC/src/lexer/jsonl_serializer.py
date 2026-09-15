"""
jsonl_serializer.py
===================

Serialização compatível com Python 3.8+.
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

from .errors import LexicalError
from .token_types import TokenType
from .tokens import Token

MAPEAMENTO_TOKENS: dict[TokenType, str] = {
    TokenType.KW_INT: "INT",
    TokenType.KW_FLOAT: "FLOAT",
    TokenType.KW_BOOL: "BOOL",
    TokenType.KW_CHAR: "CHAR",
    TokenType.KW_DOUBLE: "DOUBLE",
    TokenType.KW_VOID: "VOID",
    TokenType.KW_IF: "IF",
    TokenType.KW_ELSE: "ELSE",
    TokenType.KW_WHILE: "WHILE",
    TokenType.KW_FOR: "FOR",
    TokenType.KW_RETURN: "RETURN",
    TokenType.KW_BREAK: "BREAK",
    TokenType.KW_CONTINUE: "CONTINUE",
    TokenType.KW_TRUE: "TRUE",
    TokenType.KW_FALSE: "FALSE",
    TokenType.KW_PRINT: "PRINT",
    TokenType.KW_READ: "READ",
    TokenType.ID: "IDENT",
    TokenType.NUM_INT: "INT_LIT",
    TokenType.NUM_FLOAT: "FLOAT_LIT",
    TokenType.CHAR_LITERAL: "CHAR_LIT",
    TokenType.STRING: "STRING_LIT",
    TokenType.PLUS: "PLUS",
    TokenType.MINUS: "MINUS",
    TokenType.STAR: "STAR",
    TokenType.SLASH: "SLASH",
    TokenType.PERCENT: "PERCENT",
    TokenType.ASSIGN: "ASSIGN",
    TokenType.EQ: "EQ",
    TokenType.NEQ: "NEQ",
    TokenType.LT: "LT",
    TokenType.LE: "LE",
    TokenType.GT: "GT",
    TokenType.GE: "GE",
    TokenType.AND: "AND",
    TokenType.OR: "OR",
    TokenType.NOT: "NOT",
    TokenType.LPAREN: "LPAREN",
    TokenType.RPAREN: "RPAREN",
    TokenType.LBRACE: "LBRACE",
    TokenType.RBRACE: "RBRACE",
    TokenType.LBRACKET: "LBRACKET",
    TokenType.RBRACKET: "RBRACKET",
    TokenType.SEMI: "SEMICOLON",
    TokenType.COMMA: "COMMA",
    TokenType.DOT: "DOT",
    TokenType.EOF: "EOF",
}


def obter_nome(tipo: TokenType) -> str:
    return MAPEAMENTO_TOKENS.get(tipo, tipo.name)


def extrair_atributo(token: Token) -> int | float | str | None:
    if token.type is TokenType.ID:
        return token.lexeme
    if token.type is TokenType.NUM_INT:
        try:
            return int(token.lexeme)
        except ValueError:
            return None
    if token.type is TokenType.NUM_FLOAT:
        try:
            return float(token.lexeme)
        except ValueError:
            return None
    return token.attribute if token.attribute is not None else None


def serializar_token(token: Token) -> dict:
    return {
        "token": obter_nome(token.type),
        "lexeme": token.lexeme,
        "attribute": extrair_atributo(token),
        "line": token.line,
        "column": token.column,
    }


def serializar_erro(erro: LexicalError) -> dict:
    return {
        "error": erro.code,
        "lexeme": erro.lexeme,
        "line": erro.line,
        "column": erro.column,
    }


def serialize_tokens_jsonl(tokens: Sequence[Token]) -> str:
    tokens_validos = [t for t in tokens if t.type is not TokenType.ERROR]
    registros = [serializar_token(t) for t in tokens_validos]
    return "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in registros)


def serialize_errors_jsonl(erros: Iterable[LexicalError]) -> str:
    registros = [serializar_erro(e) for e in erros]
    return "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in registros)
