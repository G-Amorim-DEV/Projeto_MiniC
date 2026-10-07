"""AST-based semantic checking. Diagnostic presentation is separate from rules."""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from ..ast.nodes import (
    Assign, Binary, Block, Break, Call, Continue, ExprStmt, For, Function,
    Id, If, Index, Lit, Node, Parameter, Print, Program, Read, Return,
    Unary, VarDecl, While,
)

ERROR = '<error>'
NUMERIC = {'int', 'float'}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    line: int
    column: int
    message: str

    def __str__(self):
        return f'{self.code} — linha {self.line}, coluna {self.column}: {self.message}'


@dataclass
class Symbol:
    type_name: str
    name: str
    category: str
    scope: int
    line: int
    column: int
    parameters: tuple[str, ...] = ()
    dimension: Node | None = None
    declaration: Node | None = None


@dataclass
class Scope:
    number: int
    parent: Scope | None = None
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def lookup(self, name):
        scope = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


def expression_text(node: Node) -> str:
    if node.source_text:
        return node.source_text
    if isinstance(node, Id): return node.name
    if isinstance(node, Lit): return node.value
    if isinstance(node, Unary): return node.operator + expression_text(node.operand)
    if isinstance(node, Binary): return f'{expression_text(node.left)} {node.operator} {expression_text(node.right)}'
    if isinstance(node, Assign): return f'{expression_text(node.target)} = {expression_text(node.value)}'
    if isinstance(node, Index): return f'{expression_text(node.target)}[{expression_text(node.index)}]'
    if isinstance(node, Call): return expression_text(node.callee) + '(' + ', '.join(map(expression_text, node.arguments)) + ')'
    return ''


def compatible(expected: str, actual: str) -> bool:
    return ERROR in (expected, actual) or expected == actual or (expected == 'float' and actual == 'int')


class SemanticAnalyzer:
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []
        self.symbols: list[Symbol] = []
        self.scope = Scope(0)
        self.next_scope = 1
        self.function: Function | None = None
        self.loop_depth = 0

    def error(self, code, node, message):
        self.diagnostics.append(Diagnostic(code, node.line, node.column, message))

    def declare(self, node, type_name, name, category, parameters=()):
        if name in self.scope.symbols:
            previous = self.scope.symbols[name]
            self.error('SEM002', node, f'“{name}” já declarado neste escopo; declaração anterior na linha {previous.line}, coluna {previous.column} (tipo {previous.type_name}).')
            return None
        symbol = Symbol(type_name, name, category, self.scope.number, node.line, node.column, tuple(parameters),
                        node.size if isinstance(node, VarDecl) else None, node)
        node.resolved_symbol = symbol
        node.semantic_type = type_name
        self.scope.symbols[name] = symbol
        self.symbols.append(symbol)
        return symbol

    def push(self):
        self.scope = Scope(self.next_scope, self.scope)
        self.next_scope += 1

    def pop(self):
        assert self.scope.parent is not None
        self.scope = self.scope.parent

    def analyze(self, program: Program):
        # Reusable analyzer instances never retain a previous program's state.
        self.__init__()
        self._reset_annotations(program)
        for node in program.declarations:
            if isinstance(node, Function):
                self.declare(node, node.return_type, node.name, 'function',
                             (p.type_name + ('[]' if p.is_array else '') for p in node.parameters))
        for node in program.declarations:
            if not isinstance(node, Function):
                self.statement(node)
        for node in program.declarations:
            if isinstance(node, Function):
                self.function = node
                self.push()
                for p in node.parameters:
                    self.declare(p, p.type_name + ('[]' if p.is_array else ''), p.name, 'parameter')
                flow = self.block(node.body, new_scope=False)
                if node.return_type != 'void' and 'next' in flow:
                    self.missing_return(node)
                self.pop()
                self.function = None
        self.diagnostics.sort(key=lambda d: (d.line, d.column))
        return self.diagnostics

    @classmethod
    def _reset_annotations(cls, node):
        node.semantic_type = node.resolved_symbol = node.coercion_type = node.chain_coercion_type = None
        if is_dataclass(node):
            for descriptor in fields(node):
                value = getattr(node, descriptor.name)
                children = value if isinstance(value, list) else [value]
                for child in children:
                    if isinstance(child, Node): cls._reset_annotations(child)

    def conversion(self, node, expected, actual, *, context='assignment', target=None, function=None, argument=None):
        if compatible(expected, actual):
            if expected == 'float' and actual == 'int':
                if isinstance(node, Assign): node.chain_coercion_type = expected
                else: node.coercion_type = expected
            return
        text = expression_text(node)
        if context == 'argument':
            self.error('SEM008', node, f'Argumento {argument} de “{function}”: esperado {expected}, recebido {actual} (expressão “{text}”).')
        elif context == 'return':
            message = f'Retorno {actual} incompatível com o tipo {expected} da função “{function}”'
            if actual == 'float' and expected == 'int':
                message += '; conversão implícita de float para int não permitida.'
            else: message += '.'
            self.error('SEM009', node, message)
        else:
            self.error('SEM003', node, f'Não é possível atribuir {actual} a {expected} sem conversão permitida (destino “{target or text}”; expressão “{text}”).')

    def condition(self, node, kind):
        actual = self.expression(node)
        if actual not in ('bool', ERROR):
            self.error('SEM005', node, f'Condição de {kind} deve ter tipo bool; recebeu {actual} (expressão “{expression_text(node)}”).')

    def missing_return(self, node):
        message = f'A função “{node.name}” pode terminar sem retornar {node.return_type}'
        last = node.body.items[-1] if node.body.items else None
        if isinstance(last, If) and last.else_branch is None:
            message += f'; o ramo em que “{expression_text(last.condition)}” é falso alcança o fim do corpo.'
        else: message += '; há um caminho que alcança o fim do corpo.'
        self.diagnostics.append(Diagnostic('SEM011', getattr(node, 'declaration_line', node.line),
                                           getattr(node, 'declaration_column', node.column), message))

    def expression(self, node: Node, *, value=True, context='valor') -> str:
        before = len(self.diagnostics)
        result = self._assignment(node) if isinstance(node, Assign) else self._expression(node)
        if result == ERROR or len(self.diagnostics) > before:
            result = ERROR
        elif isinstance(node, Assign):
            result = 'void'
            if value:
                self.error('SEM003', node, f'A atribuição “{expression_text(node)}” é um comando sem valor e não pode ser usada como expressão.')
                result = ERROR
        elif result == 'void' and value:
            if isinstance(node, Call) and isinstance(node.callee, Id):
                self.error('SEM012', node, f'Função “{node.callee.name}” não produz valor (retorno void) e não pode ser usada como expressão de {context}.')
            else:
                self.error('SEM012', node, f'A expressão “{expression_text(node)}” de tipo void não pode ser usada como valor.')
            result = ERROR
        node.semantic_type = result
        return result

    def _assignment(self, node):
        """Check a right-to-left command chain; expose no assignment R-value."""
        before = len(self.diagnostics)
        target = self.expression(node.target)
        self.assignable(node.target, target)
        actual = self._assignment(node.value) if isinstance(node.value, Assign) else self.expression(node.value, context='atribuição')
        self.conversion(node.value, target, actual, target=expression_text(node.target))
        failed = len(self.diagnostics) > before or ERROR in (target, actual)
        node.semantic_type = ERROR if failed else 'void'
        return ERROR if failed else target

    def _expression(self, node):
        if isinstance(node, Lit): return 'float' if node.literal_type == 'real' else node.literal_type
        if isinstance(node, Id):
            symbol = self.scope.lookup(node.name)
            node.resolved_symbol = symbol
            if not symbol:
                self.error('SEM001', node, f'Identificador “{node.name}” não declarado neste escopo.')
                return ERROR
            if symbol.category == 'function':
                self.error('E_FUNCTION_VALUE', node, f"A função '{node.name}' deve ser chamada.")
                return ERROR
            return symbol.type_name
        if isinstance(node, Call):
            symbol = self.scope.lookup(node.callee.name) if isinstance(node.callee, Id) else None
            node.callee.resolved_symbol = symbol
            node.resolved_symbol = symbol
            if isinstance(node.callee, Id) and symbol is None:
                node.callee.semantic_type = ERROR
                self.error('SEM001', node.callee, f'Identificador “{node.callee.name}” não declarado neste escopo.')
            elif not symbol or symbol.category != 'function':
                if isinstance(node.callee, Id):
                    node.callee.semantic_type = ERROR
                elif self.expression(node.callee) == ERROR:
                    for arg in node.arguments: self.expression(arg)
                    return ERROR
                self.error('E_CALL', node.callee, f"'{expression_text(node.callee)}' não é uma função declarada.")
            else:
                node.callee.semantic_type = 'function'
                if len(node.arguments) != len(symbol.parameters):
                    self.error('SEM007', node, f'“{symbol.name}” espera {len(symbol.parameters)} argumentos, mas recebeu {len(node.arguments)}.')
                for i, arg in enumerate(node.arguments):
                    actual = self.expression(arg)
                    if i < len(symbol.parameters): self.conversion(arg, symbol.parameters[i], actual, context='argument', function=symbol.name, argument=i+1)
                return symbol.type_name
            for arg in node.arguments: self.expression(arg)
            return ERROR
        if isinstance(node, Index):
            target, index = self.expression(node.target), self.expression(node.index)
            if index not in ('int', ERROR):
                self.error('SEM006', node.index, f'Índice do vetor “{expression_text(node.target)}” deve ser int; recebeu {index} (expressão “{expression_text(node.index)}”).')
            if target == ERROR: return ERROR
            if not target.endswith('[]'):
                self.error('E_ARRAY', node.target, f"A expressão '{expression_text(node.target)}' não é um vetor.")
                return ERROR
            node.resolved_symbol = node.target.resolved_symbol
            return target[:-2]
        if isinstance(node, Unary):
            operand = self.expression(node.operand)
            if operand == ERROR: return ERROR
            expected = 'bool' if node.operator == '!' else 'numérico'
            if (node.operator == '!' and operand != 'bool') or (node.operator != '!' and operand not in NUMERIC):
                self.error('E_OPERATOR', node, f"O operador '{node.operator}' exige operando {expected}.")
                return ERROR
            return 'bool' if node.operator == '!' else operand
        if isinstance(node, Binary):
            left, right = self.expression(node.left), self.expression(node.right)
            if ERROR in (left, right): return ERROR
            op = node.operator
            numeric = left in NUMERIC and right in NUMERIC
            if op in ('&&', '||'): valid = left == right == 'bool'
            elif op in ('==', '!='): valid = numeric or (left == right and left in ('bool', 'char'))
            elif op == '%': valid = left == right == 'int'
            else: valid = numeric
            if not valid:
                self.error('E_OPERATOR', node, f"O operador '{op}' não aceita os tipos '{left}' e '{right}'.")
                return ERROR
            if numeric and 'float' in (left, right):
                self.conversion(node.left, 'float', left)
                self.conversion(node.right, 'float', right)
            if op in ('&&', '||', '==', '!=', '<', '<=', '>', '>='): return 'bool'
            return 'float' if 'float' in (left, right) else 'int'
        raise TypeError(f'Unsupported expression node: {type(node).__name__}')

    def assignable(self, node, type_name):
        if type_name == ERROR: return
        if not isinstance(node, (Id, Index)) or type_name.endswith('[]'):
            if isinstance(node, Lit):
                category = {'int': 'inteiro', 'real': 'real', 'bool': 'booleano', 'char': 'caractere', 'string': 'string'}[node.literal_type]
                detail = f'o literal {category} “{expression_text(node)}” não designa uma variável ou elemento de vetor.'
            else:
                detail = f'a expressão “{expression_text(node)}” não designa uma variável ou elemento de vetor.'
            self.error('SEM013', node, 'Destino de atribuição não é atribuível; ' + detail)

    def block(self, node, *, new_scope=True):
        if new_scope: self.push()
        flow = {'next'}
        for item in node.items:
            result = self.statement(item)
            if 'next' in flow: flow = (flow - {'next'}) | result
        if new_scope: self.pop()
        return flow

    def statement(self, node):
        if node is None: return {'next'}
        if isinstance(node, Block): return self.block(node)
        if isinstance(node, VarDecl):
            type_name = node.type_name + ('[]' if node.size is not None else '')
            self.declare(node, type_name, node.name, 'array' if node.size is not None else 'variable')
            if node.size is not None: self.conversion(node.size, 'int', self.expression(node.size))
            if node.initializer is not None: self.conversion(node.initializer, type_name, self.expression(node.initializer, context='atribuição'), target=node.name)
        elif isinstance(node, ExprStmt):
            if node.expression: self.expression(node.expression, value=False)
        elif isinstance(node, If):
            self.condition(node.condition, 'if')
            return self.statement(node.then_branch) | self.statement(node.else_branch)
        elif isinstance(node, (While, For)):
            if isinstance(node, For) and node.initializer: self.expression(node.initializer, value=False)
            if node.condition: self.condition(node.condition, 'for' if isinstance(node, For) else 'while')
            if isinstance(node, For) and node.increment: self.expression(node.increment, value=False)
            self.loop_depth += 1
            flow = self.statement(node.body)
            self.loop_depth -= 1
            return {'next'} | (flow & {'return'})
        elif isinstance(node, Return):
            actual = self.expression(node.value) if node.value else 'void'
            if self.function is None:
                self.error('SEM010', node, 'Retorno fora de uma função.')
            else: self.conversion(node.value or node, self.function.return_type, actual, context='return', function=self.function.name)
            return {'return'}
        elif isinstance(node, (Break, Continue)):
            if not self.loop_depth:
                keyword = 'break' if isinstance(node, Break) else 'continue'
                self.error('SEM010', node, f'{keyword} só pode ocorrer dentro de laço.')
            return {'break' if isinstance(node, Break) else 'continue'}
        elif isinstance(node, Print): self.expression(node.value)
        elif isinstance(node, Read): self.assignable(node.target, self.expression(node.target))
        else: raise TypeError(f'Unsupported statement node: {type(node).__name__}')
        return {'next'}
