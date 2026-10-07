"""Formatadores da AST do MiniC para texto compacto e em árvore."""

from __future__ import annotations

from typing import Optional

from .nodes import (
    Assign, Binary, Block, Call, ExprStmt, For, Function, Id, If, Index,
    Lit, Node, Print, Program, Read, Return, Unary, VarDecl, While,
)


def to_sexp(node: Optional[Node]) -> str:
    """Retorna a representação compacta definida pelos nós da AST."""
    return node.to_sexpr() if node is not None else "NULL"


def print_tree(node: Optional[Node], indent: int = 0) -> str:
    """Retorna a AST em formato hierárquico, com um nó por linha."""
    lines: list[str] = []

    def add(label: str, level: int) -> None:
        lines.append("  " * level + label)

    def visit(current: Optional[Node], level: int) -> None:
        if current is None:
            add("NULL", level)
            return
        if isinstance(current, Program):
            add("Program", level)
            for declaration in current.declarations:
                visit(declaration, level + 1)
        elif isinstance(current, Function):
            parameters = ", ".join(parameter.to_sexpr() for parameter in current.parameters)
            add(f"Function: {current.return_type} {current.name}({parameters})", level)
            visit(current.body, level + 1)
        elif isinstance(current, Block):
            add("Block", level)
            for item in current.items:
                visit(item, level + 1)
        elif isinstance(current, VarDecl):
            label = f"VarDecl: {current.type_name} {current.name}"
            if current.size is not None:
                label += " [size]"
            add(label, level)
            if current.size is not None:
                add("Size", level + 1)
                visit(current.size, level + 2)
            if current.initializer is not None:
                add("Initializer", level + 1)
                visit(current.initializer, level + 2)
        elif isinstance(current, If):
            add("If", level)
            add("Condition", level + 1)
            visit(current.condition, level + 2)
            add("Then", level + 1)
            visit(current.then_branch, level + 2)
            add("Else", level + 1)
            visit(current.else_branch, level + 2)
        elif isinstance(current, While):
            add("While", level)
            add("Condition", level + 1)
            visit(current.condition, level + 2)
            add("Body", level + 1)
            visit(current.body, level + 2)
        elif isinstance(current, For):
            add("For", level)
            for label, child in (
                ("Initializer", current.initializer),
                ("Condition", current.condition),
                ("Increment", current.increment),
                ("Body", current.body),
            ):
                add(label, level + 1)
                visit(child, level + 2)
        elif isinstance(current, Return):
            add("Return", level)
            visit(current.value, level + 1)
        elif isinstance(current, ExprStmt):
            add("ExprStmt", level)
            visit(current.expression, level + 1)
        elif isinstance(current, Print):
            add("Print", level)
            visit(current.value, level + 1)
        elif isinstance(current, Read):
            add("Read", level)
            visit(current.target, level + 1)
        elif isinstance(current, Assign):
            add("Assign", level)
            add("Target", level + 1)
            visit(current.target, level + 2)
            add("Value", level + 1)
            visit(current.value, level + 2)
        elif isinstance(current, Binary):
            add(f"Binary: {current.operator}", level)
            visit(current.left, level + 1)
            visit(current.right, level + 1)
        elif isinstance(current, Unary):
            add(f"Unary: {current.operator}", level)
            visit(current.operand, level + 1)
        elif isinstance(current, Call):
            add("Call", level)
            add("Callee", level + 1)
            visit(current.callee, level + 2)
            for argument in current.arguments:
                add("Argument", level + 1)
                visit(argument, level + 2)
        elif isinstance(current, Index):
            add("Index", level)
            add("Target", level + 1)
            visit(current.target, level + 2)
            add("Index expression", level + 1)
            visit(current.index, level + 2)
        elif isinstance(current, Id):
            add(f"Id: {current.name}", level)
        elif isinstance(current, Lit):
            add(f"Lit: {current.literal_type} = {current.value}", level)
        else:
            add(current.__class__.__name__, level)

    visit(node, indent)
    return "\n".join(lines)
