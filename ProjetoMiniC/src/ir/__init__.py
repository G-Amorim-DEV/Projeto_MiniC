"""Módulo de Representação Intermediária (IR) - Etapa 4 (Código de Três Endereços)."""

from .generator import IRGenerator, generate_ir
from .instructions import IRGenerationError, IRInstruction, IRProgram
from .printer import format_instruction, format_ir

__all__ = [
    "IRGenerationError",
    "IRGenerator",
    "IRInstruction",
    "IRProgram",
    "format_instruction",
    "format_ir",
    "generate_ir",
]
