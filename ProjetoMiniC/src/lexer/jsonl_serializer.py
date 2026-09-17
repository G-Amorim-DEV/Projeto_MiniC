"""
jsonl_serializer.py
===================
Módulo de conversão dos objetos `Token` e `ErroLexico` para formato JSON Lines (JSONL).
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

from .errors import ErroLexico
from .token_types import TokenType
from .tokens import Token

# Mapeamento do Enum interno de tyoes de token para nomes externos esperados nos fixtures
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
    """Resolve a string representativa do tyoe do token."""
    return MAPEAMENTO_TOKENS.get(tipo, tipo.name)


def extrair_atributo(token: Token) -> int | float | str | None:
    """Extrai e faz o casting necessário para os atributos numéricos/alfanuméricos dos tokens."""
    if token.tipo is TokenType.ID:
        return token.lexema
    if token.tipo is TokenType.NUM_INT:
        try:
            return int(token.lexema)
        except ValueError:
            return None
    if token.tipo is TokenType.NUM_FLOAT:
        try:
            return float(token.lexema)
        except ValueError:
            return None
    return token.atributo if token.atributo is not None else None


def serializar_token(token: Token) -> dict:
    """Converte a instância do token em um dicionário pré-estruturado para JSON."""
    return {
        "token": obter_nome(token.tipo),
        "lexeme": token.lexema,
        "attribute": extrair_atributo(token),
        "line": token.linha,
        "column": token.coluna,
    }


def serializar_erro(erro: ErroLexico) -> dict:
    """Converte o erro léxico no formato JSON configurado no sistema."""
    return {
        "error": erro.codigo,
        "lexeme": erro.lexema,
        "line": erro.linha,
        "column": erro.coluna,
    }


def serialize_tokens_jsonl(tokens: Sequence[Token]) -> str:
    """Serializa uma coleção completa de tokens no formato JSON Lines."""
    tokens_validos = [t for t in tokens if t.tipo is not TokenType.ERROR]
    registros = [serializar_token(t) for t in tokens_validos]
    return "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in registros)


def serialize_errors_jsonl(erros: Iterable[ErroLexico]) -> str:
    """Serializa a lista de erros capturados em JSON Lines."""
    registros = [serializar_erro(e) for e in erros]
    return "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in registros)
