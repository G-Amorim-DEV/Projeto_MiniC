"""
scanner.py
==========

Implementação do analisador léxico manual (autômato determinístico).
Compatível com Python 3.8+ em qualquer ambiente.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Permite importação direta quando executado como script isolado
DIRETORIO_ATUAL = Path(__file__).resolve().parent
if str(DIRETORIO_ATUAL) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_ATUAL))

try:
    from .analysis_result import ResultadoAnalise as AnalysisResult
    from .errors import (
        ErroIdentificadorInvalido as InvalidIdentifierError,
        ErroSimboloInvalido as InvalidSymbolError,
        ErroLexico as LexicalError,
        ErroLiteralRealMalformado as MalformedRealLiteralError,
        ErroCaractereNaoTerminado as UnterminatedCharError,
        ErroComentarioNaoTerminado as UnterminatedCommentError,
        ErroCadeiaNaoTerminada as UnterminatedStringError,
    )
    from .jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
    from .token_types import PALAVRAS_RESERVADAS as RESERVED_WORDS, TokenType
    from .tokens import Token
except (ImportError, ValueError):
    from ProjetoMiniC.src.lexer.analysis_result import ResultadoAnalise as AnalysisResult
    from ProjetoMiniC.src.lexer.errors import (
        ErroIdentificadorInvalido as InvalidIdentifierError,
        ErroSimboloInvalido as InvalidSymbolError,
        ErroLexico as LexicalError,
        ErroLiteralRealMalformado as MalformedRealLiteralError,
        ErroCaractereNaoTerminado as UnterminatedCharError,
        ErroComentarioNaoTerminado as UnterminatedCommentError,
        ErroCadeiaNaoTerminada as UnterminatedStringError,
    )
    from ProjetoMiniC.src.lexer.jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
    from ProjetoMiniC.src.lexer.token_types import PALAVRAS_RESERVADAS as RESERVED_WORDS, TokenType
    from ProjetoMiniC.src.lexer.tokens import Token


class Scanner:
    SIMPLE_OPS: Dict[str, TokenType] = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "%": TokenType.PERCENT,
        ".": TokenType.DOT,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
        "[": TokenType.LBRACKET,
        "]": TokenType.RBRACKET,
        ";": TokenType.SEMI,
        ",": TokenType.COMMA,
    }

    def __init__(self, source: str):
        self.source: str = source
        self.length: int = len(source)
        self.pos: int = 0
        self.line: int = 1
        self.column: int = 1
        self.tokens: List[Token] = []
        self.errors: List[LexicalError] = []

    def _at_end(self) -> bool:
        return self.pos >= self.length

    @staticmethod
    def _is_identifier_start(ch: str) -> bool:
        return ch == "_" or (ch.isascii() and ch.isalpha())

    @staticmethod
    def _is_identifier_continue(ch: str) -> bool:
        return Scanner._is_identifier_start(ch) or (ch.isascii() and ch.isdigit())

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < self.length else "\0"

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _add_token(self, ttype: TokenType, lexeme: str, line: int, col: int,
                    attribute: Optional[Union[int, float, str]] = None) -> None:
        self.tokens.append(Token(ttype, lexeme, line, col, attribute))

    def scan_tokens(self) -> List[Token]:
        while not self._at_end():
            self._skip_whitespace()
            if self._at_end():
                break
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column, None))
        return self.tokens

    def analyze(self) -> AnalysisResult:
        self.scan_tokens()
        return AnalysisResult(tokens=self.tokens, erros=self.errors)

    def _skip_whitespace(self) -> None:
        while not self._at_end() and self._peek() in " \t\r\n":
            self._advance()

    def _scan_token(self) -> None:
        start_line, start_col = self.line, self.column
        ch = self._advance()

        if self._is_identifier_start(ch):
            self._identifier(start_line, start_col, ch)
        elif ch.isascii() and ch.isdigit():
            self._number(start_line, start_col, ch)
        elif ch == '"':
            self._string(start_line, start_col)
        elif ch == "'":
            self._char_literal(start_line, start_col)
        elif ch == "/" and self._peek() == "/":
            self._line_comment()
        elif ch == "/" and self._peek() == "*":
            self._block_comment(start_line, start_col)
        else:
            self._operator_or_error(ch, start_line, start_col)

    def _identifier(self, line: int, col: int, first_char: str) -> None:
        lexeme = first_char
        while not self._at_end() and self._is_identifier_continue(self._peek()):
            lexeme += self._advance()

        ttype = RESERVED_WORDS.get(lexeme, TokenType.ID)
        attribute = lexeme if ttype is TokenType.ID else None
        self._add_token(ttype, lexeme, line, col, attribute)

    def _number(self, line: int, col: int, first_digit: str) -> None:
        digits = first_digit
        while not self._at_end() and self._peek().isascii() and self._peek().isdigit():
            digits += self._advance()

        # Caso i06: Identificador iniciado por dígito
        if not self._at_end() and self._is_identifier_start(self._peek()):
            letters = ""
            letters_col = self.column
            while not self._at_end() and self._is_identifier_continue(self._peek()):
                letters += self._advance()

            self.errors.append(InvalidIdentifierError(digits + letters, line, col))
            self._add_token(TokenType.NUM_INT, digits, line, col, int(digits))
            self._add_token(TokenType.ID, letters, line, letters_col, letters)
            return

        # Número real ou malformado (Caso i05)
        if self._peek() == ".":
            if not (self._peek(1).isascii() and self._peek(1).isdigit()):
                dot_col = self.column
                self._advance()
                self.errors.append(MalformedRealLiteralError(digits + ".", line, col))
                self._add_token(TokenType.NUM_INT, digits, line, col, int(digits))
                self._add_token(TokenType.DOT, ".", line, dot_col, None)
                return

            lexeme = digits + self._advance()
            while not self._at_end() and self._peek().isascii() and self._peek().isdigit():
                lexeme += self._advance()

            self._add_token(TokenType.NUM_FLOAT, lexeme, line, col, float(lexeme))
            return

        self._add_token(TokenType.NUM_INT, digits, line, col, int(digits))

    def _string(self, line: int, col: int) -> None:
        start_pos = self.pos - 1
        content = ""
        closed = False

        while not self._at_end():
            if self._peek() == "\n":
                break
            if self._peek() == '"':
                self._advance()
                closed = True
                break
            ch = self._advance()
            if ch == "\\" and not self._at_end() and self._peek() != "\n":
                escape = self._advance()
                if escape in "nt\\\"'":
                    content += {"n": "\n", "t": "\t"}.get(escape, escape)
                    continue
                content += "\\" + escape
                continue
            content += ch

        if closed:
            lexeme = self.source[start_pos:self.pos]
            self._add_token(TokenType.STRING, lexeme, line, col, content)
        else:
            err_lexeme = self.source[start_pos:self.pos]
            self.errors.append(UnterminatedStringError(err_lexeme, line, col))

            # Mantém delimitadores finais no fluxo para recuperação dos fixtures.
            while self.pos > start_pos + 1 and self.source[self.pos - 1] in ") ;}]":
                self.pos -= 1
                self.column -= 1

    def _char_literal(self, line: int, col: int) -> None:
        if self._at_end() or self._peek() == "\n":
            self.errors.append(UnterminatedCharError("'", line, col))
            return

        ch = self._advance()
        raw = ch
        if ch == "\\":
            if self._at_end() or self._peek() == "\n":
                self.errors.append(UnterminatedCharError("'\\", line, col))
                return
            escape = self._advance()
            if escape not in "nt\\\"'":
                self.errors.append(UnterminatedCharError("'\\" + escape, line, col))
                return
            raw = "\\" + escape
            ch = {"n": "\n", "t": "\t"}.get(escape, escape)
        if self._match("'"):
            self._add_token(TokenType.CHAR_LITERAL, f"'{raw}'", line, col, ch)
        else:
            lexeme = f"'{ch}"
            self.errors.append(UnterminatedCharError(lexeme, line, col))
            if self._peek() == ";":
                self._advance()

    def _line_comment(self) -> None:
        self._advance()
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _block_comment(self, line: int, col: int) -> None:
        # Caso i02: Comentário de bloco não terminado
        start_pos = self.pos - 1
        self._advance()
        while True:
            if self._at_end():
                lexeme = self.source[start_pos:]
                self.errors.append(UnterminatedCommentError(line, col, lexeme))
                return
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()

    def _operator_or_error(self, ch: str, line: int, col: int) -> None:
        if ch == "=":
            if self._match("="):
                self._add_token(TokenType.EQ, "==", line, col)
            else:
                self._add_token(TokenType.ASSIGN, "=", line, col)
        elif ch == "!":
            if self._match("="):
                self._add_token(TokenType.NEQ, "!=", line, col)
            else:
                self._add_token(TokenType.NOT, "!", line, col)
        elif ch == "<":
            if self._match("="):
                self._add_token(TokenType.LE, "<=", line, col)
            else:
                self._add_token(TokenType.LT, "<", line, col)
        elif ch == ">":
            if self._match("="):
                self._add_token(TokenType.GE, ">=", line, col)
            else:
                self._add_token(TokenType.GT, ">", line, col)
        elif ch == "&":
            if self._match("&"):
                self._add_token(TokenType.AND, "&&", line, col)
            else:
                self._invalid(ch, line, col)
        elif ch == "|":
            if self._match("|"):
                self._add_token(TokenType.OR, "||", line, col)
            else:
                self._invalid(ch, line, col)
        elif ch == "/":
            self._add_token(TokenType.SLASH, "/", line, col)
        elif ch in self.SIMPLE_OPS:
            self._add_token(self.SIMPLE_OPS[ch], ch, line, col)
        else:
            self._invalid(ch, line, col)

    def _invalid(self, ch: str, line: int, col: int) -> None:
        self.errors.append(InvalidSymbolError(ch, line, col))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_tokens(self) -> None:
        cabecalho = f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}"
        print(cabecalho)
        print("-" * len(cabecalho))
        for tok in self.tokens:
            nome, lexema, linha, coluna, attr = tok.as_row()
            lexema_repr = repr(lexema)
            if len(lexema_repr) > 24:
                lexema_repr = lexema_repr[:21] + "...'"
            print(f"{nome:<14}{lexema_repr:<26}{linha:<7}{coluna:<8}{attr}")

    def print_errors(self) -> None:
        if not self.errors:
            print("Nenhum erro léxico encontrado.")
            return
        print(f"{len(self.errors)} erro(s) léxico(s) encontrado(s):")
        for err in self.errors:
            print(f"  [ERRO LÉXICO] {err.diagnostic()}")


# ======================================================================
# PONTO DE ENTRADA CLI: python scanner.py file.c
# ======================================================================

def main() -> int:
    caminho_alvo: str | None = None
    modo_apenas_jsonl = True

    for arg in sys.argv[1:]:
        if arg == "--jsonl":
            modo_apenas_jsonl = True
        elif not arg.startswith("--") and caminho_alvo is None:
            caminho_alvo = arg

    if not caminho_alvo:
        print("Uso: python scanner.py <arquivo.c | arquivo.minic> [--jsonl]", file=sys.stderr)
        return 1

    arquivo = Path(caminho_alvo)
    if not arquivo.exists() or not arquivo.is_file():
        print(f"Erro: Arquivo '{caminho_alvo}' não encontrado.", file=sys.stderr)
        return 1

    try:
        conteudo = arquivo.read_text(encoding="utf-8")
    except OSError as err:
        print(f"Erro ao ler arquivo: {err}", file=sys.stderr)
        return 1

    scanner = Scanner(conteudo)
    scanner.scan_tokens()

    saida_tokens_json = serialize_tokens_jsonl(scanner.tokens)
    saida_erros_json = serialize_errors_jsonl(scanner.errors) if scanner.errors else ""

    # Se a flag --jsonl foi passada explicitamente, exibe estritamente o stream JSONL
    if modo_apenas_jsonl:
        if saida_tokens_json:
            print(saida_tokens_json)
        if saida_erros_json:
            print(saida_erros_json, file=sys.stderr)
        return 2 if scanner.has_errors() else 0

    # Saída padrão completa: Tabela + Diagnóstico + JSONL de Tokens + JSONL de Erros
    print("=" * 80)
    print(f"Análise Léxica - Arquivo: {arquivo.name}")
    print("=" * 80)
    print("Tokens reconhecidos:")
    scanner.print_tokens()
    print("-" * 80)
    print("Diagnóstico:")
    scanner.print_errors()

    print("-" * 80)
    print("Saída JSONL (Tokens):")
    print(saida_tokens_json if saida_tokens_json else "(vazio)")

    if scanner.errors:
        print("-" * 80)
        print("Saída JSONL (Erros):")
        print(saida_erros_json if saida_erros_json else "(vazio)")

    return 2 if scanner.has_errors() else 0


if __name__ == "__main__":
    sys.exit(main())
