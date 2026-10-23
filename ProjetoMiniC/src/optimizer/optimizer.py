"""Otimizador de Representação Intermediária (TAC) para o compilador MiniC (-O1)."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from ..ir.instructions import IRInstruction, IRProgram

_TEMP_RE = re.compile(r"^t([1-9][0-9]*)$")
_INT_RE = re.compile(r"^-?[0-9]+$")
_FLOAT_RE = re.compile(r"^-?[0-9]+\.[0-9]+$")


def _is_temp(name: Optional[str]) -> bool:
    return bool(name and _TEMP_RE.match(name))


def _is_int_lit(val: Optional[str]) -> bool:
    return bool(val and _INT_RE.match(val))


def _is_float_lit(val: Optional[str]) -> bool:
    return bool(val and _FLOAT_RE.match(val))


def _is_bool_lit(val: Optional[str]) -> bool:
    return val in ("true", "false")


def _is_numeric_or_bool_lit(val: Optional[str]) -> bool:
    return _is_int_lit(val) or _is_float_lit(val) or _is_bool_lit(val)


def _is_user_var(name: Optional[str]) -> bool:
    if not name or _is_temp(name) or _is_numeric_or_bool_lit(name):
        return False
    if name.startswith('"') or name.startswith("'"):
        return False
    return True


def _format_float(value: float) -> str:
    text = f"{value:.12g}"
    if "." not in text and "e" not in text and "E" not in text:
        text += ".0"
    return text


def _eval_unary(op: str, arg: str) -> Optional[str]:
    if op == "-":
        if _is_int_lit(arg):
            return str(-int(arg))
        if _is_float_lit(arg):
            return _format_float(-float(arg))
    elif op == "!":
        if arg == "true":
            return "false"
        if arg == "false":
            return "true"
    elif op == "int2float":
        if _is_int_lit(arg):
            return _format_float(float(int(arg)))
        if _is_float_lit(arg):
            return arg
    return None


def _eval_binary(op: str, left: str, right: str) -> Optional[str]:
    if _is_int_lit(left) and _is_int_lit(right):
        a = int(left)
        b = int(right)
        if op == "+":
            return str(a + b)
        if op == "-":
            return str(a - b)
        if op == "*":
            return str(a * b)
        if op == "/":
            if b == 0:
                return None
            return str(int(a / b))
        if op == "%":
            if b == 0:
                return None
            return str(a - int(a / b) * b)
        if op == "<":
            return "true" if a < b else "false"
        if op == "<=":
            return "true" if a <= b else "false"
        if op == ">":
            return "true" if a > b else "false"
        if op == ">=":
            return "true" if a >= b else "false"
        if op == "==":
            return "true" if a == b else "false"
        if op == "!=":
            return "true" if a != b else "false"
        return None

    if (_is_int_lit(left) or _is_float_lit(left)) and (
        _is_int_lit(right) or _is_float_lit(right)
    ):
        a = float(left)
        b = float(right)
        if op == "+":
            return _format_float(a + b)
        if op == "-":
            return _format_float(a - b)
        if op == "*":
            return _format_float(a * b)
        if op == "/":
            if b == 0.0:
                return None
            return _format_float(a / b)
        if op == "<":
            return "true" if a < b else "false"
        if op == "<=":
            return "true" if a <= b else "false"
        if op == ">":
            return "true" if a > b else "false"
        if op == ">=":
            return "true" if a >= b else "false"
        if op == "==":
            return "true" if a == b else "false"
        if op == "!=":
            return "true" if a != b else "false"
        return None

    if _is_bool_lit(left) and _is_bool_lit(right):
        a = left == "true"
        b = right == "true"
        if op == "&&":
            return "true" if (a and b) else "false"
        if op == "||":
            return "true" if (a or b) else "false"
        if op == "==":
            return "true" if (a == b) else "false"
        if op == "!=":
            return "true" if (a != b) else "false"
    return None


def _eliminate_unreachable_after_terminator(
    body: List[IRInstruction],
) -> List[IRInstruction]:
    out: List[IRInstruction] = []
    unreachable = False
    for inst in body:
        if inst.kind == "LABEL":
            unreachable = False
            out.append(inst)
            continue
        if unreachable:
            if inst.kind == "LOCAL":
                out.append(inst)
            continue
        out.append(inst)
        if inst.kind in ("RETURN", "GOTO"):
            unreachable = True
    return out


def _simplify_cfg(body: List[IRInstruction]) -> List[IRInstruction]:
    current = list(body)
    changed = True
    while changed:
        changed = False
        after_term = _eliminate_unreachable_after_terminator(current)
        if after_term != current:
            current = after_term
            changed = True

        # Remove GOTO L immediately followed by LABEL L:
        filtered: List[IRInstruction] = []
        for idx, inst in enumerate(current):
            if (
                inst.kind == "GOTO"
                and idx + 1 < len(current)
                and current[idx + 1].kind == "LABEL"
                and current[idx + 1].dest == inst.dest
            ):
                changed = True
                continue
            filtered.append(inst)
        current = filtered

        # Remove unused labels
        targeted: Set[str] = set()
        for inst in current:
            if inst.kind in ("GOTO", "IF_FALSE") and inst.dest:
                targeted.add(inst.dest)

        without_unused_labels: List[IRInstruction] = []
        for inst in current:
            if inst.kind == "LABEL" and inst.dest not in targeted:
                changed = True
                continue
            without_unused_labels.append(inst)
        current = without_unused_labels

    return current


def _simplify_algebraic_identities(body: List[IRInstruction]) -> List[IRInstruction]:
    out: List[IRInstruction] = []
    for inst in body:
        if inst.kind == "BINARY" and inst.op and inst.dest and inst.arg1 and inst.arg2:
            op = inst.op
            a1 = inst.arg1
            a2 = inst.arg2
            replacement_arg: Optional[str] = None
            if op == "+":
                if a2 in ("0", "0.0"):
                    replacement_arg = a1
                elif a1 in ("0", "0.0"):
                    replacement_arg = a2
            elif op == "-":
                if a2 in ("0", "0.0"):
                    replacement_arg = a1
                elif a1 == a2 and not _is_float_lit(a1):
                    replacement_arg = "0"
            elif op == "*":
                if a2 in ("1", "1.0"):
                    replacement_arg = a1
                elif a1 in ("1", "1.0"):
                    replacement_arg = a2
                elif a2 == "0" or a1 == "0":
                    replacement_arg = "0"
            elif op == "/":
                if a2 in ("1", "1.0"):
                    replacement_arg = a1
            elif op == "&&":
                if a2 == "true":
                    replacement_arg = a1
                elif a1 == "true":
                    replacement_arg = a2
                elif a2 == "false" or a1 == "false":
                    replacement_arg = "false"
            elif op == "||":
                if a2 == "false":
                    replacement_arg = a1
                elif a1 == "false":
                    replacement_arg = a2
                elif a2 == "true" or a1 == "true":
                    replacement_arg = "true"

            if replacement_arg is not None:
                out.append(
                    IRInstruction(
                        kind="COPY",
                        dest=inst.dest,
                        arg1=replacement_arg,
                        in_function=inst.in_function,
                    )
                )
                continue
        out.append(inst)
    return out


def _fold_constants_and_branches(body: List[IRInstruction]) -> List[IRInstruction]:
    current = list(body)
    branch_was_folded = False

    for _ in range(4):
        const_val: Dict[str, str] = {}
        is_folded: Dict[str, bool] = {}
        next_body: List[IRInstruction] = []
        folded_branch_this_round = False

        for inst in current:
            kind = inst.kind
            if kind in ("LABEL", "GOTO", "RETURN"):
                if kind == "RETURN" and inst.arg1:
                    val = const_val.get(inst.arg1)
                    if val is not None and is_folded.get(inst.arg1, False):
                        inst = IRInstruction(
                            kind="RETURN",
                            arg1=val,
                            in_function=inst.in_function,
                        )
                next_body.append(inst)
                const_val.clear()
                is_folded.clear()
                continue

            if kind == "CALL":
                next_body.append(inst)
                const_val.clear()
                is_folded.clear()
                continue

            if kind == "COPY" and inst.dest and inst.arg1:
                src = inst.arg1
                if src in const_val:
                    cval = const_val[src]
                    cfold = is_folded.get(src, False)
                    const_val[inst.dest] = cval
                    is_folded[inst.dest] = cfold
                    if cfold:
                        inst = IRInstruction(
                            kind="COPY",
                            dest=inst.dest,
                            arg1=cval,
                            in_function=inst.in_function,
                        )
                elif _is_numeric_or_bool_lit(src):
                    const_val[inst.dest] = src
                    is_folded[inst.dest] = branch_was_folded
                else:
                    const_val.pop(inst.dest, None)
                    is_folded.pop(inst.dest, None)
                next_body.append(inst)
                continue

            if kind == "UNARY" and inst.op and inst.dest and inst.arg1:
                v1 = const_val.get(inst.arg1, inst.arg1)
                folded = _eval_unary(inst.op, v1) if _is_numeric_or_bool_lit(v1) else None
                if folded is not None:
                    const_val[inst.dest] = folded
                    is_folded[inst.dest] = True
                    next_body.append(
                        IRInstruction(
                            kind="COPY",
                            dest=inst.dest,
                            arg1=folded,
                            in_function=inst.in_function,
                        )
                    )
                else:
                    const_val.pop(inst.dest, None)
                    is_folded.pop(inst.dest, None)
                    next_body.append(inst)
                continue

            if kind == "BINARY" and inst.op and inst.dest and inst.arg1 and inst.arg2:
                a1, a2 = inst.arg1, inst.arg2
                can_fold = (
                    _is_numeric_or_bool_lit(a1)
                    or _is_numeric_or_bool_lit(a2)
                    or is_folded.get(a1, False)
                    or is_folded.get(a2, False)
                )
                v1 = const_val.get(a1, a1)
                v2 = const_val.get(a2, a2)
                folded = (
                    _eval_binary(inst.op, v1, v2)
                    if (can_fold and _is_numeric_or_bool_lit(v1) and _is_numeric_or_bool_lit(v2))
                    else None
                )
                if folded is not None:
                    const_val[inst.dest] = folded
                    is_folded[inst.dest] = True
                    next_body.append(
                        IRInstruction(
                            kind="COPY",
                            dest=inst.dest,
                            arg1=folded,
                            in_function=inst.in_function,
                        )
                    )
                else:
                    const_val.pop(inst.dest, None)
                    is_folded.pop(inst.dest, None)
                    next_body.append(inst)
                continue

            if kind == "IF_FALSE" and inst.arg1 and inst.dest:
                cond_val = const_val.get(inst.arg1, inst.arg1)
                if cond_val == "true":
                    folded_branch_this_round = True
                    branch_was_folded = True
                    continue
                if cond_val == "false":
                    folded_branch_this_round = True
                    branch_was_folded = True
                    next_body.append(
                        IRInstruction(
                            kind="GOTO",
                            dest=inst.dest,
                            in_function=inst.in_function,
                        )
                    )
                    const_val.clear()
                    is_folded.clear()
                    continue
                next_body.append(inst)
                const_val.clear()
                is_folded.clear()
                continue

            if kind in ("PRINT", "ARG") and inst.arg1:
                val = const_val.get(inst.arg1)
                if val is not None and is_folded.get(inst.arg1, False):
                    inst = IRInstruction(
                        kind=kind,
                        arg1=val,
                        in_function=inst.in_function,
                    )
                next_body.append(inst)
                continue

            if kind in ("ARRAY_LOAD", "READ") and inst.dest:
                const_val.pop(inst.dest, None)
                is_folded.pop(inst.dest, None)
                next_body.append(inst)
                continue

            next_body.append(inst)

        simplified = _simplify_cfg(next_body)
        if simplified == current and not folded_branch_this_round:
            current = simplified
            break
        current = simplified

    return current


def _written_name(inst: IRInstruction) -> Optional[str]:
    if inst.kind in ("COPY", "UNARY", "BINARY", "ARRAY_LOAD"):
        return inst.dest
    if inst.kind == "CALL":
        return inst.dest
    if inst.kind == "READ" and inst.arg2 is None:
        return inst.dest
    return None


def _hoist_loop_invariant_code(
    body: List[IRInstruction], globals_set: Set[str]
) -> List[IRInstruction]:
    current = list(body)
    idx = 0
    while idx < len(current):
        inst = current[idx]
        if inst.kind != "LABEL" or not inst.dest:
            idx += 1
            continue
        label_name = inst.dest
        back_idx = -1
        for j in range(len(current) - 1, idx, -1):
            if current[j].kind == "GOTO" and current[j].dest == label_name:
                back_idx = j
                break
        if back_idx == -1:
            idx += 1
            continue

        write_counts: Dict[str, int] = {}
        has_call_or_array_store = False
        for k in range(idx + 1, back_idx):
            ins = current[k]
            if ins.kind in ("CALL", "ARRAY_STORE"):
                has_call_or_array_store = True
            w = _written_name(ins)
            if w:
                write_counts[w] = write_counts.get(w, 0) + 1
            if ins.kind == "READ" and ins.dest:
                write_counts[ins.dest] = write_counts.get(ins.dest, 0) + 1

        internal_labels = {}
        for k in range(idx + 1, back_idx):
            if current[k].kind == "LABEL" and current[k].dest:
                internal_labels[current[k].dest] = k

        conditional_indices = set()
        for k in range(idx + 1, back_idx):
            ins = current[k]
            if ins.kind in ("IF_FALSE", "GOTO") and ins.dest in internal_labels:
                target_k = internal_labels[ins.dest]
                start_k = min(k, target_k)
                end_k = max(k, target_k)
                for m in range(start_k, end_k + 1):
                    conditional_indices.add(m)

        hoisted: List[IRInstruction] = []
        kept: List[IRInstruction] = []
        for k in range(idx + 1, back_idx):
            ins = current[k]
            can_hoist = False
            if (
                ins.kind == "BINARY"
                and ins.op
                and ins.dest
                and ins.arg1
                and ins.arg2
                and _is_temp(ins.dest)
                and write_counts.get(ins.dest, 0) == 1
            ):
                if k in conditional_indices:
                    can_hoist = False
                elif (
                    k + 1 < back_idx
                    and current[k + 1].kind == "IF_FALSE"
                    and current[k + 1].arg1 == ins.dest
                ):
                    can_hoist = False
                elif ins.op in ("/", "%"):
                    if not (
                        (_is_int_lit(ins.arg2) or _is_float_lit(ins.arg2))
                        and float(ins.arg2) != 0
                    ):
                        can_hoist = False
                    elif ins.arg1 not in write_counts and ins.arg2 not in write_counts:
                        if has_call_or_array_store and (
                            ins.arg1 in globals_set or ins.arg2 in globals_set
                        ):
                            can_hoist = False
                        else:
                            can_hoist = True
                elif ins.arg1 not in write_counts and ins.arg2 not in write_counts:
                    if has_call_or_array_store and (
                        ins.arg1 in globals_set or ins.arg2 in globals_set
                    ):
                        can_hoist = False
                    else:
                        can_hoist = True

            if can_hoist and ins.dest:
                hoisted.append(ins)
                write_counts.pop(ins.dest, None)
            else:
                kept.append(ins)

        if hoisted:
            current = (
                current[:idx]
                + hoisted
                + [current[idx]]
                + kept
                + current[back_idx:]
            )
            idx += len(hoisted) + 1
        else:
            idx += 1

    return current


def _reduce_induction_variables(body: List[IRInstruction]) -> List[IRInstruction]:
    current = list(body)
    idx = 0
    while idx < len(current):
        inst = current[idx]
        if inst.kind != "LABEL" or not inst.dest:
            idx += 1
            continue
        label_name = inst.dest
        back_idx = -1
        for j in range(len(current) - 1, idx, -1):
            if current[j].kind == "GOTO" and current[j].dest == label_name:
                back_idx = j
                break
        if back_idx == -1 or back_idx - idx < 6:
            idx += 1
            continue

        has_inner_branch = False
        for k in range(idx + 1, back_idx):
            if current[k].kind in ("LABEL", "GOTO", "RETURN"):
                has_inner_branch = True
                break
            if current[k].kind == "IF_FALSE" and k > idx + 2:
                has_inner_branch = True
                break
        if has_inner_branch:
            idx += 1
            continue

        inc_bin = current[back_idx - 2]
        inc_copy = current[back_idx - 1]
        if not (
            inc_bin.kind == "BINARY"
            and inc_bin.op == "+"
            and inc_bin.dest
            and _is_temp(inc_bin.dest)
            and inc_bin.arg1
            and _is_user_var(inc_bin.arg1)
            and inc_bin.arg2
            and _is_int_lit(inc_bin.arg2)
            and inc_copy.kind == "COPY"
            and inc_copy.dest == inc_bin.arg1
            and inc_copy.arg1 == inc_bin.dest
        ):
            idx += 1
            continue

        iv = inc_bin.arg1
        step_val = int(inc_bin.arg2)

        iv_init_val: Optional[int] = None
        for p in range(idx - 1, -1, -1):
            prev = current[p]
            if prev.kind in ("LABEL", "GOTO", "IF_FALSE", "CALL", "RETURN"):
                break
            w = _written_name(prev)
            if w == iv:
                if prev.kind == "COPY" and prev.arg1 and _is_int_lit(prev.arg1):
                    iv_init_val = int(prev.arg1)
                break
        if iv_init_val is None:
            idx += 1
            continue

        iv_writes = sum(
            1 for k in range(idx + 1, back_idx) if _written_name(current[k]) == iv
        )
        if iv_writes != 1:
            idx += 1
            continue

        mul_pos = -1
        factor_val = 0
        derived_var = ""
        mul_temp = ""
        for k in range(idx + 1, back_idx - 2):
            ins1 = current[k]
            ins2 = current[k + 1]
            if (
                ins1.kind == "BINARY"
                and ins1.op == "*"
                and ins1.dest
                and _is_temp(ins1.dest)
                and ins2.kind == "COPY"
                and ins2.dest
                and _is_user_var(ins2.dest)
                and ins2.arg1 == ins1.dest
            ):
                if ins1.arg1 == iv and ins1.arg2 and _is_int_lit(ins1.arg2):
                    fval = int(ins1.arg2)
                elif ins1.arg2 == iv and ins1.arg1 and _is_int_lit(ins1.arg1):
                    fval = int(ins1.arg1)
                else:
                    continue

                cand_var = ins2.dest
                cand_writes = sum(
                    1
                    for m in range(idx + 1, back_idx)
                    if _written_name(current[m]) == cand_var
                )
                read_before = any(
                    cand_var in (current[m].arg1, current[m].arg2)
                    for m in range(idx + 1, k)
                )
                if cand_writes == 1 and not read_before:
                    mul_pos = k
                    factor_val = fval
                    derived_var = cand_var
                    mul_temp = ins1.dest
                    break

        if mul_pos == -1:
            idx += 1
            continue

        init_derived = str(iv_init_val * factor_val)
        step_derived = str(step_val * factor_val)

        init_inst = IRInstruction(
            kind="COPY",
            dest=derived_var,
            arg1=init_derived,
            in_function=inst.in_function,
        )
        inc_derived_bin = IRInstruction(
            kind="BINARY",
            op="+",
            dest=mul_temp,
            arg1=derived_var,
            arg2=step_derived,
            in_function=inst.in_function,
        )
        inc_derived_copy = IRInstruction(
            kind="COPY",
            dest=derived_var,
            arg1=mul_temp,
            in_function=inst.in_function,
        )

        new_loop_body = (
            current[idx + 1 : mul_pos]
            + current[mul_pos + 2 : back_idx]
            + [inc_derived_bin, inc_derived_copy]
        )
        current = (
            current[:idx]
            + [init_inst, current[idx]]
            + new_loop_body
            + current[back_idx:]
        )
        idx += 2

    return current


def _normalize_expr_key(
    kind: str, op: str, arg1: Optional[str], arg2: Optional[str]
) -> Tuple[str, str, str, str]:
    a1 = arg1 or ""
    a2 = arg2 or ""
    if kind == "BINARY" and op in ("+", "*", "==", "!=", "&&", "||") and a1 > a2:
        a1, a2 = a2, a1
    return (kind, op, a1, a2)


def _eliminate_common_subexpressions(
    body: List[IRInstruction],
) -> Tuple[List[IRInstruction], bool]:
    out: List[IRInstruction] = []
    avail: Dict[Tuple[str, str, str, str], str] = {}
    replaced_any = False

    def invalidate(name: str) -> None:
        to_delete = [
            key
            for key, dest_t in avail.items()
            if dest_t == name or key[2] == name or key[3] == name
        ]
        for key in to_delete:
            del avail[key]

    for inst in body:
        if inst.kind in ("LABEL", "GOTO", "IF_FALSE", "CALL", "RETURN"):
            avail.clear()
            out.append(inst)
            continue

        if inst.kind in ("BINARY", "UNARY") and inst.op and inst.dest:
            key = _normalize_expr_key(inst.kind, inst.op, inst.arg1, inst.arg2)
            existing = avail.get(key)
            if existing is not None and existing != inst.dest:
                invalidate(inst.dest)
                out.append(
                    IRInstruction(
                        kind="COPY",
                        dest=inst.dest,
                        arg1=existing,
                        in_function=inst.in_function,
                    )
                )
                replaced_any = True
                continue

            invalidate(inst.dest)
            if (
                _is_temp(inst.dest)
                and inst.arg1 != inst.dest
                and inst.arg2 != inst.dest
            ):
                avail[key] = inst.dest
            out.append(inst)
            continue

        w = _written_name(inst)
        if w:
            invalidate(w)
        if inst.kind == "READ" and inst.dest:
            invalidate(inst.dest)
        out.append(inst)

    return out, replaced_any


def _propagate_copies(body: List[IRInstruction]) -> List[IRInstruction]:
    out: List[IRInstruction] = []
    copies: Dict[str, str] = {}

    def resolve(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        visited: Set[str] = set()
        curr = val
        while curr in copies and curr not in visited:
            visited.add(curr)
            curr = copies[curr]
        return curr

    def invalidate(name: str) -> None:
        to_del = [k for k, v in copies.items() if k == name or v == name]
        for k in to_del:
            del copies[k]

    for inst in body:
        kind = inst.kind
        if kind in ("LABEL", "GOTO"):
            copies.clear()
            out.append(inst)
            continue

        if kind == "IF_FALSE":
            new_inst = IRInstruction(
                kind="IF_FALSE",
                dest=inst.dest,
                arg1=resolve(inst.arg1),
                in_function=inst.in_function,
            )
            copies.clear()
            out.append(new_inst)
            continue

        if kind == "RETURN":
            new_inst = IRInstruction(
                kind="RETURN",
                arg1=resolve(inst.arg1),
                in_function=inst.in_function,
            )
            copies.clear()
            out.append(new_inst)
            continue

        if kind == "CALL":
            copies.clear()
            out.append(inst)
            continue

        if kind == "COPY" and inst.dest and inst.arg1:
            src = resolve(inst.arg1) or inst.arg1
            new_inst = IRInstruction(
                kind="COPY",
                dest=inst.dest,
                arg1=src,
                in_function=inst.in_function,
            )
            invalidate(inst.dest)
            if inst.dest != src:
                if _is_user_var(src) or (_is_temp(inst.dest) and _is_temp(src)):
                    copies[inst.dest] = src
            out.append(new_inst)
            continue

        if kind == "UNARY" and inst.dest:
            new_inst = IRInstruction(
                kind="UNARY",
                op=inst.op,
                dest=inst.dest,
                arg1=resolve(inst.arg1),
                in_function=inst.in_function,
            )
            invalidate(inst.dest)
            out.append(new_inst)
            continue

        if kind == "BINARY" and inst.dest:
            new_inst = IRInstruction(
                kind="BINARY",
                op=inst.op,
                dest=inst.dest,
                arg1=resolve(inst.arg1),
                arg2=resolve(inst.arg2),
                in_function=inst.in_function,
            )
            invalidate(inst.dest)
            out.append(new_inst)
            continue

        if kind == "ARRAY_LOAD" and inst.dest:
            new_inst = IRInstruction(
                kind="ARRAY_LOAD",
                dest=inst.dest,
                arg1=inst.arg1,
                arg2=resolve(inst.arg2),
                in_function=inst.in_function,
            )
            invalidate(inst.dest)
            out.append(new_inst)
            continue

        if kind == "ARRAY_STORE":
            new_inst = IRInstruction(
                kind="ARRAY_STORE",
                dest=inst.dest,
                arg1=resolve(inst.arg1),
                arg2=resolve(inst.arg2),
                in_function=inst.in_function,
            )
            out.append(new_inst)
            continue

        if kind in ("PRINT", "ARG"):
            new_inst = IRInstruction(
                kind=kind,
                arg1=resolve(inst.arg1),
                in_function=inst.in_function,
            )
            out.append(new_inst)
            continue

        if kind == "READ" and inst.dest:
            invalidate(inst.dest)
            new_inst = IRInstruction(
                kind="READ",
                dest=inst.dest,
                arg2=resolve(inst.arg2),
                in_function=inst.in_function,
            )
            out.append(new_inst)
            continue

        out.append(inst)

    return out


def _collect_reads(inst: IRInstruction) -> Set[str]:
    reads: Set[str] = set()
    kind = inst.kind
    if kind in ("COPY", "UNARY", "IF_FALSE", "ARG", "RETURN", "PRINT"):
        if inst.arg1:
            reads.add(inst.arg1)
    elif kind == "BINARY":
        if inst.arg1:
            reads.add(inst.arg1)
        if inst.arg2:
            reads.add(inst.arg2)
    elif kind == "ARRAY_LOAD":
        if inst.arg1:
            reads.add(inst.arg1)
        if inst.arg2:
            reads.add(inst.arg2)
    elif kind == "ARRAY_STORE":
        if inst.dest:
            reads.add(inst.dest)
        if inst.arg1:
            reads.add(inst.arg1)
        if inst.arg2:
            reads.add(inst.arg2)
    elif kind == "READ":
        if inst.dest:
            reads.add(inst.dest)
        if inst.arg2:
            reads.add(inst.arg2)
    return reads


def _eliminate_dead_stores(
    body: List[IRInstruction], globals_set: Set[str]
) -> List[IRInstruction]:
    current = list(body)
    changed = True
    while changed:
        changed = False
        all_reads: Set[str] = set()
        for inst in current:
            all_reads.update(_collect_reads(inst))

        next_body: List[IRInstruction] = []
        for inst in current:
            if inst.kind == "COPY" and inst.dest == inst.arg1:
                changed = True
                continue
            if inst.kind in ("COPY", "UNARY", "BINARY", "ARRAY_LOAD") and inst.dest:
                if inst.dest not in all_reads and inst.dest not in globals_set:
                    changed = True
                    continue
            next_body.append(inst)
        current = next_body

    referenced: Set[str] = set()
    for inst in current:
        if inst.kind == "LOCAL":
            continue
        referenced.update(_collect_reads(inst))
        w = _written_name(inst)
        if w:
            referenced.add(w)
        if inst.kind == "READ" and inst.dest:
            referenced.add(inst.dest)

    final_body: List[IRInstruction] = []
    for inst in current:
        if inst.kind == "LOCAL" and inst.arg2 is None and inst.dest:
            if inst.dest not in referenced:
                continue
        final_body.append(inst)

    return final_body


def _renumber_temps_if_needed(body: List[IRInstruction]) -> List[IRInstruction]:
    reserved: Set[str] = set()
    temps_in_order: List[str] = []
    seen_temps: Set[str] = set()

    def inspect_token(tok: Optional[str]) -> None:
        if not tok:
            return
        m = _TEMP_RE.match(tok)
        if m:
            if tok not in seen_temps:
                seen_temps.add(tok)
                temps_in_order.append(tok)
        elif _is_user_var(tok):
            reserved.add(tok)

    for inst in body:
        if inst.kind in ("PARAM", "LOCAL") and inst.dest:
            reserved.add(inst.dest)
            continue
        if inst.kind not in ("LABEL", "GOTO", "IF_FALSE", "CALL"):
            inspect_token(inst.dest)
        inspect_token(inst.arg1)
        inspect_token(inst.arg2)

    if not temps_in_order:
        return body

    max_idx = max(int(_TEMP_RE.match(t).group(1)) for t in temps_in_order)  # type: ignore[union-attr]
    if len(temps_in_order) == max_idx:
        return body

    mapping: Dict[str, str] = {}
    counter = 0
    for old_t in temps_in_order:
        while True:
            counter += 1
            cand = f"t{counter}"
            if cand not in reserved:
                mapping[old_t] = cand
                break

    def remap(tok: Optional[str]) -> Optional[str]:
        if tok is None:
            return None
        return mapping.get(tok, tok)

    out: List[IRInstruction] = []
    for inst in body:
        new_dest = (
            inst.dest
            if inst.kind in ("LABEL", "GOTO", "IF_FALSE", "PARAM", "LOCAL")
            else remap(inst.dest)
        )
        out.append(
            IRInstruction(
                kind=inst.kind,
                op=inst.op,
                dest=new_dest,
                arg1=remap(inst.arg1),
                arg2=remap(inst.arg2),
                in_function=inst.in_function,
            )
        )
    return out


def _optimize_function_body(
    body: List[IRInstruction], globals_set: Set[str]
) -> List[IRInstruction]:
    step1 = _simplify_cfg(body)
    step2 = _simplify_algebraic_identities(step1)
    step3 = _fold_constants_and_branches(step2)
    step4 = _hoist_loop_invariant_code(step3, globals_set)
    step5 = _reduce_induction_variables(step4)
    step6, cse_applied = _eliminate_common_subexpressions(step5)
    step7 = _propagate_copies(step6)
    step8 = _simplify_algebraic_identities(step7)
    step9 = _propagate_copies(step8)
    step10 = _eliminate_dead_stores(step9, globals_set)
    if cse_applied:
        step10 = _renumber_temps_if_needed(step10)
    return step10


class IROptimizer:
    """Aplica passes clássicos de otimização sobre um `IRProgram` no modo `-O1`."""

    def optimize(self, program: IRProgram) -> IRProgram:
        if not isinstance(program, IRProgram):
            raise TypeError("IROptimizer.optimize espera uma instância de IRProgram.")

        globals_set: Set[str] = set()
        for inst in program.instructions:
            if inst.kind == "GLOBAL" and inst.dest:
                globals_set.add(inst.dest)

        optimized = IRProgram()
        idx = 0
        n = len(program.instructions)
        while idx < n:
            inst = program.instructions[idx]
            if inst.kind == "FUNC_BEGIN":
                optimized.append(inst)
                idx += 1
                body: List[IRInstruction] = []
                while idx < n and program.instructions[idx].kind != "FUNC_END":
                    body.append(program.instructions[idx])
                    idx += 1
                opt_body = _optimize_function_body(body, globals_set)
                for b_inst in opt_body:
                    optimized.append(b_inst)
                if idx < n and program.instructions[idx].kind == "FUNC_END":
                    optimized.append(program.instructions[idx])
                    idx += 1
            else:
                optimized.append(inst)
                idx += 1

        return optimized


def optimize_ir(program: IRProgram) -> IRProgram:
    """Atalho funcional para otimizar um `IRProgram` (modo `-O1`)."""
    return IROptimizer().optimize(program)
