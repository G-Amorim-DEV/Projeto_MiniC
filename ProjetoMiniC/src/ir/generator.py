"""Gerador de Representação Intermediária (IR) em Código de Três Endereços (TAC)."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..ast.nodes import (
    Assign,
    Binary,
    Block,
    Break,
    Call,
    Continue,
    ExprStmt,
    For,
    Function,
    Id,
    If,
    Index,
    Lit,
    Node,
    Parameter,
    Print,
    Program,
    Read,
    Return,
    Unary,
    VarDecl,
    While,
)
from .instructions import IRGenerationError, IRInstruction, IRProgram

ERROR_TYPE = "<error>"


class IRGenerator:
    """Converte uma AST semanticamente validada e anotada em um IRProgram (TAC)."""

    def __init__(self) -> None:
        self.program_ir = IRProgram()
        self._temp_counter = 0
        self._label_counter = 0
        self._in_function = False
        self._loop_stack: List[Tuple[str, str]] = []
        self._decl_names: Dict[int, str] = {}
        self._global_var_names: Set[str] = set()
        self._seen_in_scope_group: Set[str] = set()
        self._reserved_names: Set[str] = set()

    def generate(self, program: Program) -> IRProgram:
        """Valida a AST anotada e gera o programa em Representação Intermediária."""
        self.__init__()
        self._validate_ast(program)
        self._collect_reserved_names(program)

        for decl in program.declarations:
            if isinstance(decl, VarDecl):
                self._decl_names[id(decl)] = decl.name
                self._global_var_names.add(decl.name)

        self._seen_in_scope_group = set(self._global_var_names)

        for decl in program.declarations:
            if isinstance(decl, Function):
                self._emit_function(decl)
            else:
                self._emit_statement(decl)

        return self.program_ir

    def _collect_reserved_names(self, program: Program) -> None:
        for node in self._walk(program):
            if isinstance(node, (Function, VarDecl, Parameter)):
                self._reserved_names.add(node.name)
                symbol = getattr(node, "resolved_symbol", None)
                scope = getattr(symbol, "scope", 0)
                if scope and scope > 0:
                    self._reserved_names.add(f"{node.name}${scope}")
            elif isinstance(node, Id):
                self._reserved_names.add(node.name)

    def _new_temp(self) -> str:
        while True:
            self._temp_counter += 1
            candidate = f"t{self._temp_counter}"
            if candidate not in self._reserved_names:
                self._reserved_names.add(candidate)
                return candidate

    def _new_label(self) -> str:
        while True:
            self._label_counter += 1
            candidate = f"L{self._label_counter}"
            if candidate not in self._reserved_names:
                self._reserved_names.add(candidate)
                return candidate

    def _emit(
        self,
        kind: str,
        *,
        op: Optional[str] = None,
        dest: Optional[str] = None,
        arg1: Optional[str] = None,
        arg2: Optional[str] = None,
        in_function: Optional[bool] = None,
    ) -> None:
        self.program_ir.append(
            IRInstruction(
                kind=kind,
                op=op,
                dest=dest,
                arg1=arg1,
                arg2=arg2,
                in_function=self._in_function if in_function is None else in_function,
            )
        )

    def _validate_ast(self, program: object) -> None:
        if not isinstance(program, Program):
            raise IRGenerationError("AST inválida: o nó raiz deve ser uma instância de Program.")
        if not program.declarations:
            raise IRGenerationError("AST inválida ou vazia: nenhuma declaração encontrada.")

        annotated_nodes = 0
        self._validate_node(program, in_func=False, loop_depth=0)
        for node in self._walk(program):
            if isinstance(
                node,
                (Function, VarDecl, Parameter, Id, Lit, Unary, Binary, Assign, Call, Index),
            ):
                annotated_nodes += 1
                if node.semantic_type is None:
                    raise IRGenerationError(
                        f"AST sem análise semântica: nó {type(node).__name__} na linha {node.line}, coluna {node.column} não possui tipo semântico."
                    )
                if node.semantic_type == ERROR_TYPE:
                    raise IRGenerationError(
                        f"AST contém erro semântico na linha {node.line}, coluna {node.column}."
                    )
            if isinstance(node, (Function, VarDecl, Parameter, Id, Call)):
                if node.resolved_symbol is None:
                    raise IRGenerationError(
                        f"AST sem resolução de símbolos: nó {type(node).__name__} na linha {node.line}, coluna {node.column}."
                    )

        if annotated_nodes == 0:
            raise IRGenerationError(
                "AST sem anotações semânticas: execute o SemanticAnalyzer antes de gerar IR."
            )

    def _validate_node(self, node: Optional[Node], *, in_func: bool, loop_depth: int) -> None:
        if node is None:
            return
        if isinstance(node, Program):
            for decl in node.declarations:
                self._validate_node(decl, in_func=False, loop_depth=0)
            return
        if isinstance(node, Function):
            for param in node.parameters:
                self._validate_node(param, in_func=True, loop_depth=0)
            self._validate_node(node.body, in_func=True, loop_depth=0)
            return
        if isinstance(node, Block):
            for item in node.items:
                self._validate_node(item, in_func=in_func, loop_depth=loop_depth)
            return
        if isinstance(node, (While, For)):
            if isinstance(node, For):
                self._validate_node(node.initializer, in_func=in_func, loop_depth=loop_depth)
                self._validate_node(node.condition, in_func=in_func, loop_depth=loop_depth)
                self._validate_node(node.increment, in_func=in_func, loop_depth=loop_depth)
            else:
                self._validate_node(node.condition, in_func=in_func, loop_depth=loop_depth)
            self._validate_node(node.body, in_func=in_func, loop_depth=loop_depth + 1)
            return
        if isinstance(node, If):
            self._validate_node(node.condition, in_func=in_func, loop_depth=loop_depth)
            self._validate_node(node.then_branch, in_func=in_func, loop_depth=loop_depth)
            self._validate_node(node.else_branch, in_func=in_func, loop_depth=loop_depth)
            return
        if isinstance(node, Return):
            if not in_func:
                raise IRGenerationError("AST inválida: comando 'return' fora de função.")
            self._validate_node(node.value, in_func=in_func, loop_depth=loop_depth)
            return
        if isinstance(node, (Break, Continue)):
            if loop_depth <= 0:
                raise IRGenerationError("AST inválida: comando 'break'/'continue' fora de laço.")
            return

    @classmethod
    def _walk(cls, node: Node):
        yield node
        if is_dataclass(node):
            for descriptor in fields(node):
                value = getattr(node, descriptor.name)
                children = value if isinstance(value, list) else [value]
                for child in children:
                    if isinstance(child, Node):
                        yield from cls._walk(child)

    def _register_scoped_decl(self, decl: Node, name: str) -> str:
        symbol = getattr(decl, "resolved_symbol", None)
        scope = getattr(symbol, "scope", 0)
        if scope == 0:
            ir_name = name
            self._global_var_names.add(name)
            self._seen_in_scope_group.add(name)
        elif name not in self._seen_in_scope_group:
            self._seen_in_scope_group.add(name)
            ir_name = name
        else:
            ir_name = f"{name}${scope}"
        self._decl_names[id(decl)] = ir_name
        return ir_name

    def _resolve_var_name(self, node: Node) -> str:
        symbol = getattr(node, "resolved_symbol", None)
        decl = getattr(symbol, "declaration", None)
        if decl is not None and id(decl) in self._decl_names:
            return self._decl_names[id(decl)]
        if isinstance(node, Id):
            return node.name
        raise IRGenerationError(f"Não foi possível resolver o símbolo para o nó {type(node).__name__}.")

    def _emit_function(self, func: Function) -> None:
        prev_in_function = self._in_function
        prev_seen = self._seen_in_scope_group
        self._in_function = False
        self._seen_in_scope_group = set(self._global_var_names)

        self._emit("FUNC_BEGIN", dest=func.name, arg1=func.return_type, in_function=False)
        self._in_function = True

        for param in func.parameters:
            ir_name = self._register_scoped_decl(param, param.name)
            param_type = param.type_name + ("[]" if param.is_array else "")
            self._emit("PARAM", dest=ir_name, arg1=param_type)

        for item in func.body.items:
            self._emit_statement(item)

        self._in_function = False
        self._emit("FUNC_END", in_function=False)

        self._in_function = prev_in_function
        self._seen_in_scope_group = prev_seen

    def _emit_statement(self, node: Optional[Node]) -> None:
        if node is None:
            return

        if isinstance(node, Block):
            for item in node.items:
                self._emit_statement(item)
            return

        if isinstance(node, VarDecl):
            symbol = getattr(node, "resolved_symbol", None)
            scope = getattr(symbol, "scope", 0)
            is_global = scope == 0
            ir_name = (
                self._decl_names.get(id(node))
                if is_global and id(node) in self._decl_names
                else self._register_scoped_decl(node, node.name)
            )
            decl_kind = "GLOBAL" if is_global else "LOCAL"
            if node.size is not None:
                size_val = self._emit_expr(node.size)
                self._emit(
                    decl_kind,
                    dest=ir_name,
                    arg1=node.type_name,
                    arg2=size_val,
                    in_function=False if is_global else self._in_function,
                )
            else:
                self._emit(
                    decl_kind,
                    dest=ir_name,
                    arg1=node.type_name,
                    in_function=False if is_global else self._in_function,
                )
                if node.initializer is not None:
                    init_val = self._emit_expr(node.initializer)
                    self._emit("COPY", dest=ir_name, arg1=init_val)
            return

        if isinstance(node, ExprStmt):
            if node.expression is not None:
                if isinstance(node.expression, Assign):
                    self._emit_assign(node.expression)
                else:
                    self._emit_expr(node.expression)
            return

        if isinstance(node, If):
            if node.else_branch is None:
                end_label = self._new_label()
                cond_val = self._emit_expr(node.condition)
                self._emit("IF_FALSE", dest=end_label, arg1=cond_val)
                self._emit_statement(node.then_branch)
                self._emit("LABEL", dest=end_label)
            else:
                else_label = self._new_label()
                end_label = self._new_label()
                cond_val = self._emit_expr(node.condition)
                self._emit("IF_FALSE", dest=else_label, arg1=cond_val)
                self._emit_statement(node.then_branch)
                self._emit("GOTO", dest=end_label)
                self._emit("LABEL", dest=else_label)
                self._emit_statement(node.else_branch)
                self._emit("LABEL", dest=end_label)
            return

        if isinstance(node, While):
            start_label = self._new_label()
            end_label = self._new_label()
            self._emit("LABEL", dest=start_label)
            cond_val = self._emit_expr(node.condition)
            self._emit("IF_FALSE", dest=end_label, arg1=cond_val)
            self._loop_stack.append((start_label, end_label))
            self._emit_statement(node.body)
            self._loop_stack.pop()
            self._emit("GOTO", dest=start_label)
            self._emit("LABEL", dest=end_label)
            return

        if isinstance(node, For):
            if node.initializer is not None:
                if isinstance(node.initializer, Assign):
                    self._emit_assign(node.initializer)
                else:
                    self._emit_expr(node.initializer)
            start_label = self._new_label()
            step_label = self._new_label()
            end_label = self._new_label()
            self._emit("LABEL", dest=start_label)
            if node.condition is not None:
                cond_val = self._emit_expr(node.condition)
                self._emit("IF_FALSE", dest=end_label, arg1=cond_val)
            self._loop_stack.append((step_label, end_label))
            self._emit_statement(node.body)
            self._loop_stack.pop()
            self._emit("LABEL", dest=step_label)
            if node.increment is not None:
                if isinstance(node.increment, Assign):
                    self._emit_assign(node.increment)
                else:
                    self._emit_expr(node.increment)
            self._emit("GOTO", dest=start_label)
            self._emit("LABEL", dest=end_label)
            return

        if isinstance(node, Return):
            if node.value is not None:
                ret_val = self._emit_expr(node.value)
                self._emit("RETURN", arg1=ret_val)
            else:
                self._emit("RETURN")
            return

        if isinstance(node, Break):
            if not self._loop_stack:
                raise IRGenerationError("AST inválida: 'break' fora de laço.")
            _, break_label = self._loop_stack[-1]
            self._emit("GOTO", dest=break_label)
            return

        if isinstance(node, Continue):
            if not self._loop_stack:
                raise IRGenerationError("AST inválida: 'continue' fora de laço.")
            continue_label, _ = self._loop_stack[-1]
            self._emit("GOTO", dest=continue_label)
            return

        if isinstance(node, Print):
            val = self._emit_expr(node.value)
            self._emit("PRINT", arg1=val)
            return

        if isinstance(node, Read):
            if isinstance(node.target, Index):
                arr_name = self._resolve_var_name(node.target.target)
                idx_val = self._emit_expr(node.target.index)
                self._emit("READ", dest=arr_name, arg2=idx_val)
            elif isinstance(node.target, Id):
                var_name = self._resolve_var_name(node.target)
                self._emit("READ", dest=var_name)
            else:
                raise IRGenerationError("Destino inválido em comando 'read'.")
            return

        raise IRGenerationError(f"Comando AST não suportado na geração de IR: {type(node).__name__}")

    def _emit_assign(self, node: Assign) -> str:
        if isinstance(node.target, Index):
            arr_name = self._resolve_var_name(node.target.target)
            idx_val = self._emit_expr(node.target.index)
            target_is_index = True
            var_name = ""
        elif isinstance(node.target, Id):
            var_name = self._resolve_var_name(node.target)
            arr_name = ""
            idx_val = ""
            target_is_index = False
        else:
            raise IRGenerationError("Destino de atribuição inválido na geração de IR.")

        if isinstance(node.value, Assign):
            rhs_val = self._emit_assign(node.value)
            if node.value.chain_coercion_type == "float":
                coerced = self._new_temp()
                self._emit("UNARY", op="int2float", dest=coerced, arg1=rhs_val)
                rhs_val = coerced
        else:
            rhs_val = self._emit_expr(node.value)

        if target_is_index:
            self._emit("ARRAY_STORE", dest=arr_name, arg1=idx_val, arg2=rhs_val)
            return rhs_val
        else:
            self._emit("COPY", dest=var_name, arg1=rhs_val)
            return var_name

    def _emit_expr(self, node: Node) -> str:
        val = self._emit_expr_raw(node)
        if node.coercion_type == "float":
            temp = self._new_temp()
            self._emit("UNARY", op="int2float", dest=temp, arg1=val)
            return temp
        return val

    def _emit_expr_raw(self, node: Node) -> str:
        if isinstance(node, Lit):
            if node.source_text:
                return node.source_text
            if node.literal_type == "char" and not (
                node.value.startswith("'") and node.value.endswith("'")
            ):
                return f"'{node.value}'"
            if node.literal_type == "string" and not (
                node.value.startswith('"') and node.value.endswith('"')
            ):
                return f'"{node.value}"'
            return str(node.value)

        if isinstance(node, Id):
            return self._resolve_var_name(node)

        if isinstance(node, Unary):
            operand_val = self._emit_expr(node.operand)
            temp = self._new_temp()
            self._emit("UNARY", op=node.operator, dest=temp, arg1=operand_val)
            return temp

        if isinstance(node, Binary):
            left_val = self._emit_expr(node.left)
            right_val = self._emit_expr(node.right)
            temp = self._new_temp()
            self._emit("BINARY", op=node.operator, dest=temp, arg1=left_val, arg2=right_val)
            return temp

        if isinstance(node, Index):
            arr_name = self._resolve_var_name(node.target)
            idx_val = self._emit_expr(node.index)
            temp = self._new_temp()
            self._emit("ARRAY_LOAD", dest=temp, arg1=arr_name, arg2=idx_val)
            return temp

        if isinstance(node, Call):
            if not isinstance(node.callee, Id):
                raise IRGenerationError("Alvo de chamada inválido na geração de IR.")
            func_name = node.callee.name
            arg_vals = [self._emit_expr(arg) for arg in node.arguments]
            for arg_val in arg_vals:
                self._emit("ARG", arg1=arg_val)
            arity_str = str(len(arg_vals))
            if node.semantic_type == "void":
                self._emit("CALL", arg1=func_name, arg2=arity_str)
                return ""
            temp = self._new_temp()
            self._emit("CALL", dest=temp, arg1=func_name, arg2=arity_str)
            return temp

        if isinstance(node, Assign):
            return self._emit_assign(node)

        raise IRGenerationError(f"Expressão AST não suportada na geração de IR: {type(node).__name__}")


def generate_ir(program: Program) -> IRProgram:
    """Função utilitária para gerar um IRProgram a partir de uma AST semanticamente válida."""
    return IRGenerator().generate(program)

