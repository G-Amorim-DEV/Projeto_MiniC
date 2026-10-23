"""Estruturas de dados da Representação Intermediária (IR) em código de três endereços (TAC)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class IRGenerationError(ValueError):
    """Erro lançado quando o gerador de IR recebe uma AST inválida ou não anotada pela análise semântica."""


@dataclass(frozen=True)
class IRInstruction:
    """Instrução individual de código de três endereços (TAC)."""

    kind: str
    op: Optional[str] = None
    dest: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    in_function: bool = False


@dataclass
class IRProgram:
    """Programa em Representação Intermediária composto por uma sequência linear de instruções TAC."""

    instructions: List[IRInstruction] = field(default_factory=list)

    def append(self, instruction: IRInstruction) -> None:
        self.instructions.append(instruction)

    def to_tac(self) -> str:
        from .printer import format_ir
        return format_ir(self)

    def __str__(self) -> str:
        return self.to_tac()

