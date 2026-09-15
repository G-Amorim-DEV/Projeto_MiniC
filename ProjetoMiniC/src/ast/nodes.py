"""Nós tipados e serialização S-expression da AST do MiniC."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class Node:
    def to_sexpr(self) -> str:
        raise NotImplementedError


def _join(values: List[Node]) -> str:
    return ",".join(value.to_sexpr() for value in values)


@dataclass
class Program(Node):
    declarations: List[Node] = field(default_factory=list)
    def to_sexpr(self) -> str: return "Program(" + _join(self.declarations) + ")"


@dataclass
class Block(Node):
    items: List[Node] = field(default_factory=list)
    def to_sexpr(self) -> str: return "Block(" + _join(self.items) + ")"


@dataclass
class VarDecl(Node):
    type_name: str
    name: str
    initializer: Optional[Node] = None
    size: Optional[Node] = None
    def to_sexpr(self) -> str:
        name = self.name if self.size is None else self.name + "[" + self.size.to_sexpr() + "]"
        values = [self.type_name + " " + name]
        if self.initializer is not None: values.append(self.initializer.to_sexpr())
        return "VarDecl(" + ",".join(values) + ")"


@dataclass
class Parameter(Node):
    type_name: str
    name: str
    is_array: bool = False
    def to_sexpr(self) -> str: return self.type_name + " " + self.name + ("[]" if self.is_array else "")


@dataclass
class Function(Node):
    return_type: str
    name: str
    parameters: List[Parameter]
    body: Block
    def to_sexpr(self) -> str:
        signature = self.return_type + " " + self.name + "(" + ",".join(p.to_sexpr() for p in self.parameters) + ")"
        return "Function(" + signature + " " + self.body.to_sexpr() + ")"


@dataclass
class Id(Node):
    name: str
    def to_sexpr(self) -> str: return "Id(" + self.name + ")"


@dataclass
class Lit(Node):
    value: str
    def to_sexpr(self) -> str: return "Lit(" + self.value + ")"


@dataclass
class Unary(Node):
    operator: str
    operand: Node
    def to_sexpr(self) -> str: return "Unary(" + self.operator + "," + self.operand.to_sexpr() + ")"


@dataclass
class Binary(Node):
    operator: str
    left: Node
    right: Node
    def to_sexpr(self) -> str: return "Binary(" + self.operator + "," + self.left.to_sexpr() + "," + self.right.to_sexpr() + ")"


@dataclass
class Assign(Node):
    target: Node
    value: Node
    def to_sexpr(self) -> str: return "Assign(" + self.target.to_sexpr() + "," + self.value.to_sexpr() + ")"


@dataclass
class Call(Node):
    callee: Node
    arguments: List[Node]
    def to_sexpr(self) -> str: return "Call(" + self.callee.to_sexpr() + ("," if self.arguments else "") + _join(self.arguments) + ")"


@dataclass
class Index(Node):
    target: Node
    index: Node
    def to_sexpr(self) -> str: return "Index(" + self.target.to_sexpr() + "," + self.index.to_sexpr() + ")"


@dataclass
class ExprStmt(Node):
    expression: Optional[Node]
    def to_sexpr(self) -> str: return "ExprStmt(" + (self.expression.to_sexpr() if self.expression else "NULL") + ")"


@dataclass
class If(Node):
    condition: Node
    then_branch: Node
    else_branch: Optional[Node] = None
    def to_sexpr(self) -> str:
        parts = [self.condition.to_sexpr(), self.then_branch.to_sexpr()]
        if self.else_branch is not None: parts.append(self.else_branch.to_sexpr())
        return "If(" + ",".join(parts) + ")"


@dataclass
class While(Node):
    condition: Node
    body: Node
    def to_sexpr(self) -> str: return "While(" + self.condition.to_sexpr() + "," + self.body.to_sexpr() + ")"


@dataclass
class For(Node):
    initializer: Optional[Node]
    condition: Optional[Node]
    increment: Optional[Node]
    body: Node
    def to_sexpr(self) -> str:
        parts = [self.initializer, self.condition, self.increment, self.body]
        return "For(" + ",".join(p.to_sexpr() if p else "NULL" for p in parts) + ")"


@dataclass
class Return(Node):
    value: Optional[Node]
    def to_sexpr(self) -> str: return "Return(" + (self.value.to_sexpr() if self.value else "NULL") + ")"


@dataclass
class Print(Node):
    value: Node
    def to_sexpr(self) -> str: return "Print(" + self.value.to_sexpr() + ")"


@dataclass
class Read(Node):
    target: Node
    def to_sexpr(self) -> str: return "Read(" + self.target.to_sexpr() + ")"


class Break(Node):
    def to_sexpr(self) -> str: return "Break()"


class Continue(Node):
    def to_sexpr(self) -> str: return "Continue()"
