"""
scanner.py
==========
Mecanismo principal de análise léxica (Scanner). Converte o código fonte
em uma lista sequencial de tokens e identifica violações sintáticas/léxicas.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

DIRETORIO_ATUAL = Path(__file__).resolve().parent
if str(DIRETORIO_ATUAL) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_ATUAL))

try:
    from .analysis_result import ResultadoAnalise
    from .errors import (
        ErroCaractereNaoTerminado,
        ErroCadeiaNaoTerminada,
        ErroComentarioNaoTerminado,
        ErroIdentificadorInvalido,
        ErroLexico,
        ErroLiteralRealMalformado,
        ErroSimboloInvalido,
    )
    from .jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
    from .token_types import PALAVRAS_RESERVADAS, TokenType
    from .tokens import Token
except (ImportError, ValueError):
    from ProjetoMiniC.src.lexer.analysis_result import ResultadoAnalise
    from ProjetoMiniC.src.lexer.errors import (
        ErroCaractereNaoTerminado,
        ErroCadeiaNaoTerminada,
        ErroComentarioNaoTerminado,
        ErroIdentificadorInvalido,
        ErroLexico,
        ErroLiteralRealMalformado,
        ErroSimboloInvalido,
    )
    from ProjetoMiniC.src.lexer.jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
    from ProjetoMiniC.src.lexer.token_types import PALAVRAS_RESERVADAS, TokenType
    from ProjetoMiniC.src.lexer.tokens import Token


class Scanner:
    """Analisador léxico por autômato finito determinístico de leitura direta."""

    OPERADORES_SIMPLES: Dict[str, TokenType] = {
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

    def __init__(self, codigo_fonte: str):
        self.codigo_fonte: str = codigo_fonte
        self.source: str = codigo_fonte
        self.tamanho: int = len(codigo_fonte)
        self.length: int = self.tamanho
        self.posicao: int = 0
        self.pos: int = 0
        self.linha: int = 1
        self.line: int = 1
        self.coluna: int = 1
        self.column: int = 1
        self.tokens: List[Token] = []
        self.erros: List[ErroLexico] = []
        self.errors: List[ErroLexico] = self.erros

    def _esta_no_fim(self) -> bool:
        return self._at_end()

    def _espiar(self, offset: int = 0) -> str:
        return self._peek(offset)

    def _avancar(self) -> str:
        return self._advance()

    def _ignorar_espacos_em_branco(self) -> None:
        self._skip_whitespace()

    def _processar_proximo_token(self) -> None:
        self._scan_token()

    def _adicionar_token(self, tipo: TokenType, lexema: str, linha: int, coluna: int,
                         atributo: Optional[Union[int, float, str]] = None) -> None:
        self._add_token(tipo, lexema, linha, coluna, atributo)

    def _add_token(self, tipo: TokenType, lexema: str, linha: int, coluna: int,
                   atributo: Optional[Union[int, float, str]] = None) -> None:
        self.tokens.append(Token(tipo, lexema, linha, coluna, atributo))

    def _compara_e_avanca(self, esperado: str) -> bool:
        if self._peek() == esperado:
            self._advance()
            return True
        return False

    def _match(self, expected: str) -> bool:
        return self._compara_e_avanca(expected)

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
        if self._at_end():
            raise IndexError("avançar além do fim da fonte")
        ch = self.source[self.pos]
        self.pos += 1
        self.posicao = self.pos
        if ch == "\n":
            self.line += 1
            self.column = 1
            self.linha = self.line
            self.coluna = self.column
        else:
            self.column += 1
            self.coluna = self.column
        return ch

    def scan_tokens(self) -> List[Token]:
        while not self._at_end():
            self._skip_whitespace()
            if self._at_end():
                break
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", self.linha, self.coluna, None))
        return self.tokens

    def analisar(self) -> ResultadoAnalise:
        self.scan_tokens()
        return ResultadoAnalise(tokens=self.tokens, erros=self.erros)

    def _skip_whitespace(self) -> None:
        while not self._at_end() and self._peek() in " \t\r\n":
            self._advance()

    def _line_comment(self) -> None:
        self._advance()
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _block_comment(self, linha: int, coluna: int) -> None:
        posicao_inicial = self.posicao - 1
        self._advance()
        while True:
            if self._at_end():
                lexema = self.codigo_fonte[posicao_inicial:]
                self.erros.append(ErroComentarioNaoTerminado(linha, coluna, lexema))
                return
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()

    def _processar_comentario_linha(self) -> None:
        self._line_comment()

    def _processar_comentario_bloco(self, linha: int, coluna: int) -> None:
        self._block_comment(linha, coluna)

    def _scan_token(self) -> None:
        start_line, start_col = self.linha, self.coluna
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

        ttype = PALAVRAS_RESERVADAS.get(lexeme, TokenType.ID)
        attribute = lexeme if ttype is TokenType.ID else None
        self._add_token(ttype, lexeme, line, col, attribute)

    def _number(self, line: int, col: int, first_digit: str) -> None:
        digits = first_digit
        while not self._at_end() and self._peek().isascii() and self._peek().isdigit():
            digits += self._advance()

        if not self._at_end() and self._is_identifier_start(self._peek()):
            letters = ""
            letters_col = self.coluna
            while not self._at_end() and self._is_identifier_continue(self._peek()):
                letters += self._advance()
            self.erros.append(ErroIdentificadorInvalido(digits + letters, line, col))
            self._add_token(TokenType.NUM_INT, digits, line, col, int(digits))
            self._add_token(TokenType.ID, letters, line, letters_col, letters)
            return

        if self._peek() == ".":
            if not (self._peek(1).isascii() and self._peek(1).isdigit()):
                dot_col = self.coluna
                self._advance()
                self.erros.append(ErroLiteralRealMalformado(digits + ".", line, col))
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
            self.erros.append(ErroCadeiaNaoTerminada(err_lexeme, line, col))
            # Preserve trailing delimiters, matching the C scanner and fixtures.
            while self.pos > start_pos and self.source[self.pos - 1] in ") ;}]":
                self.pos -= 1
                self.column -= 1
            self.posicao, self.coluna = self.pos, self.column

    def _char_literal(self, line: int, col: int) -> None:
        if self._at_end() or self._peek() == "\n":
            self.erros.append(ErroCaractereNaoTerminado("'", line, col))
            return

        ch = self._advance()
        raw = ch
        if ch == "\\":
            if self._at_end() or self._peek() == "\n":
                self.erros.append(ErroCaractereNaoTerminado("'\\", line, col))
                return
            escape = self._advance()
            if escape not in "nt\\\"'":
                self.erros.append(ErroCaractereNaoTerminado("'\\" + escape, line, col))
                return
            raw = "\\" + escape
            ch = {"n": "\n", "t": "\t"}.get(escape, escape)
        if self._match("'"):
            self._add_token(TokenType.CHAR_LITERAL, f"'{raw}'", line, col, ch)
        else:
            self.erros.append(ErroCaractereNaoTerminado(f"'{raw}", line, col))
            if self._peek() == ";":
                self._advance()

    def _processar_operador_ou_erro(self, caractere: str, linha: int, coluna: int) -> None:
        self._operator_or_error(caractere, linha, coluna)

    def _operator_or_error(self, caractere: str, linha: int, coluna: int) -> None:
        if caractere == "=":
            if self._compara_e_avanca("="):
                self._add_token(TokenType.EQ, "==", linha, coluna)
            else:
                self._add_token(TokenType.ASSIGN, "=", linha, coluna)
        elif caractere == "!":
            if self._compara_e_avanca("="):
                self._add_token(TokenType.NEQ, "!=", linha, coluna)
            else:
                self._add_token(TokenType.NOT, "!", linha, coluna)
        elif caractere == "<":
            if self._compara_e_avanca("="):
                self._add_token(TokenType.LE, "<=", linha, coluna)
            else:
                self._add_token(TokenType.LT, "<", linha, coluna)
        elif caractere == ">":
            if self._compara_e_avanca("="):
                self._add_token(TokenType.GE, ">=", linha, coluna)
            else:
                self._add_token(TokenType.GT, ">", linha, coluna)
        elif caractere == "&":
            if self._compara_e_avanca("&"):
                self._add_token(TokenType.AND, "&&", linha, coluna)
            else:
                self._invalid_symbol(caractere, linha, coluna)
        elif caractere == "|":
            if self._compara_e_avanca("|"):
                self._add_token(TokenType.OR, "||", linha, coluna)
            else:
                self._invalid_symbol(caractere, linha, coluna)
        elif caractere == "/":
            self._add_token(TokenType.SLASH, "/", linha, coluna)
        elif caractere in self.OPERADORES_SIMPLES:
            self._add_token(self.OPERADORES_SIMPLES[caractere], caractere, linha, coluna)
        else:
            self._invalid_symbol(caractere, linha, coluna)

    def _invalid_symbol(self, caractere: str, linha: int, coluna: int) -> None:
        self.erros.append(ErroSimboloInvalido(caractere, linha, coluna))

    def _sinalizar_invalido(self, caractere: str, linha: int, coluna: int) -> None:
        self._invalid_symbol(caractere, linha, coluna)

    def possui_erros(self) -> bool:
        return len(self.erros) > 0

    def imprimir_tokens(self) -> None:
        cabecalho = f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}"
        print(cabecalho)
        print("-" * len(cabecalho))
        for token in self.tokens:
            nome, lexema, linha, coluna, atributo = token.para_linha_tabela()
            lexema_repr = repr(lexema)
            if len(lexema_repr) > 24:
                lexema_repr = lexema_repr[:21] + "...'"
            print(f"{nome:<14}{lexema_repr:<26}{linha:<7}{coluna:<8}{atributo}")

    def imprimir_erros(self) -> None:
        if not self.erros:
            print("Nenhum erro léxico encontrado.")
            return
        print(f"{len(self.erros)} erro(s) léxico(s) encontrado(s):")
        for erro in self.erros:
            print(f"  [ERRO LÉXICO] {erro.diagnostico()}")


def main() -> int:
    """Função de entrada do CLI ao rodar diretamente o módulo scanner.py."""
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
    saida_erros_json = serialize_errors_jsonl(scanner.erros) if scanner.erros else ""

    if modo_apenas_jsonl:
        if saida_tokens_json:
            print(saida_tokens_json)
        if saida_erros_json:
            print(saida_erros_json, file=sys.stderr)
        return 2 if scanner.possui_erros() else 0

    print("=" * 80)
    print(f"Análise Léxica - Arquivo: {arquivo.name}")
    print("=" * 80)
    print("Tokens reconhecidos:")
    scanner.imprimir_tokens()
    print("-" * 80)
    print("Diagnóstico:")
    scanner.imprimir_erros()

    print("-" * 80)
    print("Saída JSONL (Tokens):")
    print(saida_tokens_json if saida_tokens_json else "(vazio)")

    if scanner.erros:
        print("-" * 80)
        print("Saída JSONL (Erros):")
        print(saida_erros_json if saida_erros_json else "(vazio)")

    return 2 if scanner.possui_erros() else 0


if __name__ == "__main__":
    sys.exit(main())
