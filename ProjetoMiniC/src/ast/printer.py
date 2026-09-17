"""
printer.py
==========
Funções utilitárias para serializar a AST em texto legível, nos dois
formatos sugeridos pelo tutorial de conversão tokens->AST:

  1. Forma parentetizada (S-expression), útil para testes automatizados
     que comparam a AST produzida com uma AST esperada em texto:
         (ASSIGN x (PLUS (INT 1) (STAR (INT 2) (INT 3))))

  2. Forma em árvore indentada, útil para inspeção humana de um programa
     completo:
         Program
           FunctionDecl: main
             Block
               ReturnStmt
                 Literal: 0
"""

from __future__ import annotations

from typing import Optional

from . import nodes as no

# Mapeamento do lexema do operador para o símbolo usado na forma parentetizada.
_OPERADORES_BINARIOS = {
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
    "==": "EQ", "!=": "NEQ", "<": "LT", "<=": "LE", ">": "GT", ">=": "GE",
    "&&": "AND", "||": "OR",
}
_OPERADORES_UNARIOS = {"-": "NEG", "!": "NOT"}


def _sexp_alvo(alvo: no.NoAST) -> str:
    """Formata o alvo de uma atribuição/leitura (Identifier ou ArrayAccess)."""
    if isinstance(alvo, no.Identifier):
        return alvo.nome
    return to_sexp(alvo)


def to_sexp(node: Optional[no.NoAST]) -> str:
    """Converte um nó (ou subárvore) da AST para a forma parentetizada (S-expression)."""
    if node is None:
        return "NULL"

    if isinstance(node, no.Literal):
        rotulo = {
            "int": "INT", "float": "FLOAT", "bool": "BOOL",
            "char": "CHAR", "string": "STRING",
        }.get(node.tipo_literal, node.tipo_literal.upper())
        return f"({rotulo} {node.valor})"

    if isinstance(node, no.Identifier):
        return node.nome

    if isinstance(node, no.BinaryOp):
        simbolo = _OPERADORES_BINARIOS.get(node.operador, node.operador)
        return f"({simbolo} {to_sexp(node.esquerda)} {to_sexp(node.direita)})"

    if isinstance(node, no.UnaryOp):
        simbolo = _OPERADORES_UNARIOS.get(node.operador, node.operador)
        return f"({simbolo} {to_sexp(node.operando)})"

    if isinstance(node, no.Assignment):
        return f"(ASSIGN {_sexp_alvo(node.alvo)} {to_sexp(node.valor)})"

    if isinstance(node, no.CallExpr):
        args = " ".join(to_sexp(a) for a in node.argumentos)
        return f"(CALL {node.nome_funcao}{' ' + args if args else ''})"

    if isinstance(node, no.ArrayAccess):
        return f"(INDEX {to_sexp(node.vetor)} {to_sexp(node.indice)})"

    if isinstance(node, no.ExprStmt):
        return to_sexp(node.expressao) if node.expressao is not None else "(EMPTY)"

    if isinstance(node, no.ReturnStmt):
        return f"(RETURN {to_sexp(node.valor)})" if node.valor is not None else "(RETURN)"

    if isinstance(node, no.PrintStmt):
        return f"(PRINT {to_sexp(node.valor)})"

    if isinstance(node, no.ReadStmt):
        return f"(READ {_sexp_alvo(node.alvo)})"

    if isinstance(node, no.BreakStmt):
        return "(BREAK)"

    if isinstance(node, no.ContinueStmt):
        return "(CONTINUE)"

    if isinstance(node, no.VarDecl):
        partes = [f"(VARDECL {node.tipo} {node.nome}"]
        if node.eh_vetor:
            partes.append(f"[{to_sexp(node.tamanho_vetor)}]")
        if node.inicializador is not None:
            partes.append(to_sexp(node.inicializador))
        return " ".join(partes) + ")"

    if isinstance(node, no.IfStmt):
        if node.senao is not None:
            return f"(IF {to_sexp(node.condicao)} {to_sexp(node.entao)} {to_sexp(node.senao)})"
        return f"(IF {to_sexp(node.condicao)} {to_sexp(node.entao)})"

    if isinstance(node, no.WhileStmt):
        return f"(WHILE {to_sexp(node.condicao)} {to_sexp(node.corpo)})"

    if isinstance(node, no.ForStmt):
        return (f"(FOR {to_sexp(node.inicializacao)} {to_sexp(node.condicao)} "
                f"{to_sexp(node.incremento)} {to_sexp(node.corpo)})")

    if isinstance(node, no.Block):
        comandos = " ".join(to_sexp(c) for c in node.comandos)
        return f"(BLOCK {comandos})" if comandos else "(BLOCK)"

    if isinstance(node, no.Param):
        sufixo = "[]" if node.eh_vetor else ""
        return f"({node.tipo} {node.nome}{sufixo})"

    if isinstance(node, no.FunctionDecl):
        params = " ".join(to_sexp(p) for p in node.parametros)
        return f"(FUNCTION {node.tipo_retorno} {node.nome} ({params}) {to_sexp(node.corpo)})"

    if isinstance(node, no.Program):
        decls = " ".join(to_sexp(d) for d in node.declarations)
        return f"(PROGRAM {decls})"

    return f"(? {node!r})"


def print_tree(node: Optional[no.NoAST], indent: int = 0) -> str:
    """Gera uma representação em árvore indentada, legível para inspeção humana."""
    prefixo = "  " * indent
    if node is None:
        return f"{prefixo}NULL"

    linhas = []

    def add(texto: str) -> None:
        linhas.append(f"{prefixo}{texto}")

    if isinstance(node, no.Program):
        add("Program")
        for decl in node.declarations:
            linhas.append(print_tree(decl, indent + 1))
    elif isinstance(node, no.FunctionDecl):
        params = ", ".join(f"{p.tipo} {p.nome}{'[]' if p.eh_vetor else ''}" for p in node.parametros)
        add(f"FunctionDecl: {node.tipo_retorno} {node.nome}({params})")
        linhas.append(print_tree(node.corpo, indent + 1))
    elif isinstance(node, no.VarDecl):
        sufixo = f"[{to_sexp(node.tamanho_vetor)}]" if node.eh_vetor else ""
        add(f"VarDecl: {node.tipo} {node.nome}{sufixo}")
        if node.inicializador is not None:
            linhas.append(print_tree(node.inicializador, indent + 1))
    elif isinstance(node, no.Block):
        add("Block")
        for cmd in node.comandos:
            linhas.append(print_tree(cmd, indent + 1))
    elif isinstance(node, no.IfStmt):
        add("IfStmt")
        linhas.append(print_tree(node.condicao, indent + 1))
        linhas.append(print_tree(node.entao, indent + 1))
        if node.senao is not None:
            linhas.append(print_tree(node.senao, indent + 1))
    elif isinstance(node, no.WhileStmt):
        add("WhileStmt")
        linhas.append(print_tree(node.condicao, indent + 1))
        linhas.append(print_tree(node.corpo, indent + 1))
    elif isinstance(node, no.ForStmt):
        add("ForStmt")
        linhas.append(print_tree(node.inicializacao, indent + 1))
        linhas.append(print_tree(node.condicao, indent + 1))
        linhas.append(print_tree(node.incremento, indent + 1))
        linhas.append(print_tree(node.corpo, indent + 1))
    elif isinstance(node, no.ReturnStmt):
        add("ReturnStmt")
        if node.valor is not None:
            linhas.append(print_tree(node.valor, indent + 1))
    elif isinstance(node, no.BreakStmt):
        add("BreakStmt")
    elif isinstance(node, no.ContinueStmt):
        add("ContinueStmt")
    elif isinstance(node, no.PrintStmt):
        add("PrintStmt")
        linhas.append(print_tree(node.valor, indent + 1))
    elif isinstance(node, no.ReadStmt):
        add("ReadStmt")
        linhas.append(print_tree(node.alvo, indent + 1))
    elif isinstance(node, no.ExprStmt):
        add("ExprStmt")
        if node.expressao is not None:
            linhas.append(print_tree(node.expressao, indent + 1))
    elif isinstance(node, no.Assignment):
        add("Assignment")
        linhas.append(print_tree(node.alvo, indent + 1))
        linhas.append(print_tree(node.valor, indent + 1))
    elif isinstance(node, no.BinaryOp):
        add(f"BinaryOp: {node.operador}")
        linhas.append(print_tree(node.esquerda, indent + 1))
        linhas.append(print_tree(node.direita, indent + 1))
    elif isinstance(node, no.UnaryOp):
        add(f"UnaryOp: {node.operador}")
        linhas.append(print_tree(node.operando, indent + 1))
    elif isinstance(node, no.Literal):
        add(f"Literal({node.tipo_literal}): {node.valor}")
    elif isinstance(node, no.Identifier):
        add(f"Identifier: {node.nome}")
    elif isinstance(node, no.CallExpr):
        add(f"CallExpr: {node.nome_funcao}")
        for arg in node.argumentos:
            linhas.append(print_tree(arg, indent + 1))
    elif isinstance(node, no.ArrayAccess):
        add("ArrayAccess")
        linhas.append(print_tree(node.vetor, indent + 1))
        linhas.append(print_tree(node.indice, indent + 1))
    else:
        add(repr(node))

    return "\n".join(linhas)
