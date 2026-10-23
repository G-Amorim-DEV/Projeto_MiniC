"""Formatação textual determinística de Código de Três Endereços (TAC)."""

from __future__ import annotations

from typing import Union

from .instructions import IRInstruction, IRProgram


def format_instruction(inst: IRInstruction) -> str:
    """Formata uma única instrução IR para sua representação textual TAC."""
    indent = "  " if inst.in_function else ""
    kind = inst.kind

    if kind == "GLOBAL":
        if inst.arg2 is not None:
            return f"global {inst.arg1} {inst.dest}[{inst.arg2}]"
        return f"global {inst.arg1} {inst.dest}"

    if kind == "FUNC_BEGIN":
        return f"func {inst.arg1} {inst.dest}:"

    if kind == "FUNC_END":
        return "endfunc"

    if kind == "PARAM":
        return f"{indent}param {inst.arg1} {inst.dest}"

    if kind == "LOCAL":
        if inst.arg2 is not None:
            return f"{indent}local {inst.arg1} {inst.dest}[{inst.arg2}]"
        return f"{indent}local {inst.arg1} {inst.dest}"

    if kind == "COPY":
        return f"{indent}{inst.dest} = {inst.arg1}"

    if kind == "UNARY":
        return f"{indent}{inst.dest} = {inst.op} {inst.arg1}"

    if kind == "BINARY":
        return f"{indent}{inst.dest} = {inst.arg1} {inst.op} {inst.arg2}"

    if kind == "ARRAY_LOAD":
        return f"{indent}{inst.dest} = {inst.arg1}[{inst.arg2}]"

    if kind == "ARRAY_STORE":
        return f"{indent}{inst.dest}[{inst.arg1}] = {inst.arg2}"

    if kind == "LABEL":
        return f"{indent}{inst.dest}:"

    if kind == "GOTO":
        return f"{indent}goto {inst.dest}"

    if kind == "IF_FALSE":
        return f"{indent}if_false {inst.arg1} goto {inst.dest}"

    if kind == "ARG":
        return f"{indent}arg {inst.arg1}"

    if kind == "CALL":
        if inst.dest:
            return f"{indent}{inst.dest} = call {inst.arg1}, {inst.arg2}"
        return f"{indent}call {inst.arg1}, {inst.arg2}"

    if kind == "RETURN":
        if inst.arg1 is not None and inst.arg1 != "":
            return f"{indent}return {inst.arg1}"
        return f"{indent}return"

    if kind == "PRINT":
        return f"{indent}print {inst.arg1}"

    if kind == "READ":
        if inst.arg2 is not None:
            return f"{indent}read {inst.dest}[{inst.arg2}]"
        return f"{indent}read {inst.dest}"

    raise ValueError(f"Tipo de instrução IR desconhecido: {kind}")


def format_ir(ir_program: Union[IRProgram, list[IRInstruction]]) -> str:
    """Converte um IRProgram (ou lista de instruções) em texto TAC determinístico."""
    instructions = (
        ir_program.instructions
        if isinstance(ir_program, IRProgram)
        else ir_program
    )
    return "\n".join(format_instruction(inst) for inst in instructions)

