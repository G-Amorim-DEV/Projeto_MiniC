"""Parser descendente recursivo para os tokens produzidos pelo lexer MiniC."""

from __future__ import annotations

from typing import List, Optional, Sequence

from ProjetoMiniC.src.ast import (
    Assign, Binary, Block, Break, Call, Continue, ExprStmt, For, Function, Id,
    If, Index, Lit, Parameter, Print, Program, Read, Return, Unary, VarDecl,
    While,
)
from ProjetoMiniC.src.lexer.token_types import TokenType
from ProjetoMiniC.src.lexer.tokens import Token


TYPE_TOKENS = (TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_CHAR)


class SyntaxErrorMiniC(Exception):
    """Diagnóstico sintático com a posição do token que provocou a falha."""

    def __init__(self, token: Token, expected: str):
        self.token = token
        self.expected = expected
        found = "EOF" if token.type is TokenType.EOF else repr(token.lexeme)
        super().__init__("Erro sintático na linha {}, coluna {}: esperado {}; encontrado {}".format(token.line, token.column, expected, found))


class Parser:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = list(tokens)
        self.current = 0
        self.errors: List[SyntaxErrorMiniC] = []

    def parse(self) -> Optional[Program]:
        declarations = []
        while not self._at_end():
            try:
                declarations.append(self._top_level())
            except SyntaxErrorMiniC as error:
                self.errors.append(error)
                self._synchronize()
        return Program(declarations) if not self.errors else None

    def _top_level(self):
        if not self._check_any(TYPE_TOKENS + (TokenType.KW_VOID,)):
            raise self._error(self._peek(), "uma declaração global ou função")
        type_token = self._advance()
        if type_token.type is TokenType.KW_VOID:
            return self._function_after_type(type_token)
        name = self._consume(TokenType.ID, "identificador após o tipo")
        if self._match(TokenType.LPAREN):
            return self._function_after_open(type_token, name)
        return self._global_after_name(type_token, name)

    def _function_after_type(self, type_token: Token):
        name = self._consume(TokenType.ID, "identificador após 'void'")
        self._consume(TokenType.LPAREN, "'(' após o nome da função")
        return self._function_after_open(type_token, name)

    def _function_after_open(self, type_token: Token, name: Token) -> Function:
        parameters = self._parameters()
        self._consume(TokenType.RPAREN, "')' após os parâmetros")
        body = self._block()
        return Function(type_token.lexeme, name.lexeme, parameters, body)

    def _parameters(self) -> List[Parameter]:
        parameters = []
        if self._check(TokenType.RPAREN): return parameters
        while True:
            type_token = self._consume_any(TYPE_TOKENS, "tipo do parâmetro")
            name = self._consume(TokenType.ID, "identificador do parâmetro")
            is_array = False
            if self._match(TokenType.LBRACKET):
                self._consume(TokenType.RBRACKET, "']' após '[' no parâmetro")
                is_array = True
            parameters.append(Parameter(type_token.lexeme, name.lexeme, is_array))
            if not self._match(TokenType.COMMA): break
            if self._check(TokenType.RPAREN): raise self._error(self._peek(), "parâmetro após ','")
        return parameters

    def _global_after_name(self, type_token: Token, name: Token) -> VarDecl:
        declaration = self._declarator(type_token.lexeme, name)
        self._consume(TokenType.SEMI, "';' após declaração global")
        return declaration

    def _block(self) -> Block:
        self._consume(TokenType.LBRACE, "'{' para iniciar bloco")
        items = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            try:
                items.extend(self._local_declaration() if self._check_any(TYPE_TOKENS) else [self._statement()])
            except SyntaxErrorMiniC as error:
                self.errors.append(error)
                self._synchronize()
        self._consume(TokenType.RBRACE, "'}' para encerrar bloco")
        return Block(items)

    def _local_declaration(self) -> List[VarDecl]:
        type_name = self._advance().lexeme
        declarations = [self._declarator(type_name, self._consume(TokenType.ID, "identificador na declaração local"))]
        while self._match(TokenType.COMMA):
            declarations.append(self._declarator(type_name, self._consume(TokenType.ID, "identificador após ','")))
        self._consume(TokenType.SEMI, "';' após declaração local")
        return declarations

    def _declarator(self, type_name: str, name: Token) -> VarDecl:
        size = None
        if self._match(TokenType.LBRACKET):
            size = self._expression()
            self._consume(TokenType.RBRACKET, "']' após o tamanho do vetor")
        initializer = self._expression() if self._match(TokenType.ASSIGN) else None
        return VarDecl(type_name, name.lexeme, initializer, size)

    def _statement(self):
        if self._match(TokenType.LBRACE):
            self.current -= 1
            return self._block()
        if self._match(TokenType.KW_IF): return self._if_statement()
        if self._match(TokenType.KW_WHILE): return self._while_statement()
        if self._match(TokenType.KW_FOR): return self._for_statement()
        if self._match(TokenType.KW_RETURN): return self._return_statement()
        if self._match(TokenType.KW_BREAK):
            self._consume(TokenType.SEMI, "';' após break")
            return Break()
        if self._match(TokenType.KW_CONTINUE):
            self._consume(TokenType.SEMI, "';' após continue")
            return Continue()
        if self._match(TokenType.KW_PRINT): return self._print_statement()
        if self._match(TokenType.KW_READ): return self._read_statement()
        if self._match(TokenType.KW_ELSE): raise self._error(self._previous(), "'if' antes de 'else'")
        expression = None if self._check(TokenType.SEMI) else self._expression()
        self._consume(TokenType.SEMI, "';' após expressão")
        return ExprStmt(expression)

    def _if_statement(self):
        self._consume(TokenType.LPAREN, "'(' após if")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "')' após a condição")
        then_branch = self._statement()
        else_branch = self._statement() if self._match(TokenType.KW_ELSE) else None
        return If(condition, then_branch, else_branch)

    def _while_statement(self):
        self._consume(TokenType.LPAREN, "'(' após while")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "')' após a condição")
        if self._check(TokenType.EOF): raise self._error(self._peek(), "corpo após while")
        return While(condition, self._statement())

    def _for_statement(self):
        self._consume(TokenType.LPAREN, "'(' após for")
        initializer = None if self._check(TokenType.SEMI) else self._expression()
        self._consume(TokenType.SEMI, "';' após inicialização do for")
        condition = None if self._check(TokenType.SEMI) else self._expression()
        self._consume(TokenType.SEMI, "';' após condição do for")
        increment = None if self._check(TokenType.RPAREN) else self._expression()
        self._consume(TokenType.RPAREN, "')' após cláusulas do for")
        return For(initializer, condition, increment, self._statement())

    def _return_statement(self):
        value = None if self._check(TokenType.SEMI) else self._expression()
        self._consume(TokenType.SEMI, "';' após return")
        return Return(value)

    def _print_statement(self):
        self._consume(TokenType.LPAREN, "'(' após print")
        value = self._expression()
        self._consume(TokenType.RPAREN, "')' após argumento de print")
        self._consume(TokenType.SEMI, "';' após print")
        return Print(value)

    def _read_statement(self):
        self._consume(TokenType.LPAREN, "'(' após read")
        target = self._postfix()
        if not isinstance(target, (Id, Index)): raise self._error(self._previous(), "localizável como argumento de read")
        self._consume(TokenType.RPAREN, "')' após argumento de read")
        self._consume(TokenType.SEMI, "';' após read")
        return Read(target)

    def _expression(self): return self._assignment()
    def _assignment(self):
        expression = self._or()
        if self._match(TokenType.ASSIGN):
            equals = self._previous()
            value = self._assignment()
            if not isinstance(expression, (Id, Index)): raise self._error(equals, "localizável antes de '='")
            return Assign(expression, value)
        return expression
    def _or(self): return self._left(self._and, (TokenType.OR,))
    def _and(self): return self._left(self._equality, (TokenType.AND,))
    def _equality(self): return self._left(self._relational, (TokenType.EQ, TokenType.NEQ))
    def _relational(self): return self._left(self._additive, (TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE))
    def _additive(self): return self._left(self._multiplicative, (TokenType.PLUS, TokenType.MINUS))
    def _multiplicative(self): return self._left(self._unary, (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT))
    def _left(self, next_rule, operators):
        expression = next_rule()
        while self._match(*operators):
            operator = self._previous()
            expression = Binary(operator.lexeme, expression, next_rule())
        return expression
    def _unary(self):
        if self._match(TokenType.MINUS, TokenType.NOT): return Unary(self._previous().lexeme, self._unary())
        return self._postfix()
    def _postfix(self):
        expression = self._primary()
        while True:
            if self._match(TokenType.LBRACKET):
                index = self._expression()
                self._consume(TokenType.RBRACKET, "']' após índice")
                expression = Index(expression, index)
            elif self._match(TokenType.LPAREN):
                arguments = []
                if not self._check(TokenType.RPAREN):
                    arguments.append(self._expression())
                    while self._match(TokenType.COMMA): arguments.append(self._expression())
                self._consume(TokenType.RPAREN, "')' após argumentos")
                expression = Call(expression, arguments)
            else: break
        return expression
    def _primary(self):
        if self._match(TokenType.ID): return Id(self._previous().lexeme)
        if self._match(TokenType.NUM_INT, TokenType.NUM_FLOAT, TokenType.KW_TRUE, TokenType.KW_FALSE, TokenType.CHAR_LITERAL, TokenType.STRING): return Lit(self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expression = self._expression()
            self._consume(TokenType.RPAREN, "')' após expressão")
            return expression
        raise self._error(self._peek(), "expressão")

    def _synchronize(self):
        # Sempre consome ao menos o token que provocou a falha. Sem esse
        # avanço, um token que também inicia um comando (por exemplo ``{``)
        # faria o modo pânico repetir o mesmo diagnóstico indefinidamente.
        if not self._at_end():
            self._advance()
        while not self._at_end():
            if self._previous().type in (TokenType.SEMI, TokenType.RBRACE): return
            if self._peek().type in TYPE_TOKENS + (TokenType.KW_VOID, TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN, TokenType.KW_BREAK, TokenType.KW_CONTINUE, TokenType.KW_PRINT, TokenType.KW_READ, TokenType.LBRACE): return
            self._advance()
    def _match(self, *types):
        if self._check_any(types): self._advance(); return True
        return False
    def _consume(self, token_type, expected):
        if self._check(token_type): return self._advance()
        raise self._error(self._peek(), expected)
    def _consume_any(self, types, expected):
        if self._check_any(types): return self._advance()
        raise self._error(self._peek(), expected)
    def _check(self, token_type): return not self._at_end() and self._peek().type is token_type
    def _check_any(self, types): return any(self._check(token_type) for token_type in types)
    def _advance(self):
        if not self._at_end(): self.current += 1
        return self._previous()
    def _at_end(self): return self._peek().type is TokenType.EOF
    def _peek(self): return self.tokens[self.current]
    def _previous(self): return self.tokens[self.current - 1]
    def _error(self, token, expected): return SyntaxErrorMiniC(token, expected)
