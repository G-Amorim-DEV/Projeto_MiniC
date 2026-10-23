"""Avaliador oficial da suíte de 30 casos de IR e Otimização (`minic-ir-test-cases`).

Valida:
1. `01-validos-sem-otimizacao` (P01..P10): compilação com `--ir` (-O0), comparação estrutural
   normalizada contra a IR canônica do gabarito e simulação em máquina virtual TAC.
2. `02-erros` (E01..E10): rejeição obrigatória, validação da categoria e código de saída
   (2 = léxico, 3 = sintático, 4 = semântico) e ausência de emissão de IR.
3. `03-otimizacoes` (O01..O10): compilação com `-O1 --ir`, equivalência semântica/observável
   entre `-O0` e `-O1` via simulação TAC e verificação estrutural da transformação-alvo.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent


def find_gcc() -> str:
    cc_env = os.environ.get("CC")
    if cc_env:
        found_cc = shutil.which(cc_env)
        if found_cc:
            return found_cc
    found = shutil.which("gcc")
    if found:
        return found
    for candidate in (
        "C:/msys64/ucrt64/bin/gcc.exe",
        "C:/msys64/mingw64/bin/gcc.exe",
        "C:/MinGW/bin/gcc.exe",
    ):
        if Path(candidate).is_file():
            return candidate
    return "gcc"


@dataclass
class SimResult:
    prints: List[str]
    return_value: Optional[str]


def _eval_sim_val(tok: str, env: Dict[str, object]) -> object:
    tok = tok.strip()
    if tok in env:
        return env[tok]
    if tok == "true":
        return True
    if tok == "false":
        return False
    if re.match(r"^-?[0-9]+$", tok):
        return int(tok)
    if re.match(r"^-?[0-9]+\.[0-9]+$", tok):
        return float(tok)
    if (tok.startswith('"') and tok.endswith('"')) or (
        tok.startswith("'") and tok.endswith("'")
    ):
        return tok[1:-1]
    return 0


def simulate_tac(tac_text: str) -> SimResult:
    """Executa um programa TAC em uma máquina virtual para validar sua semântica observável."""
    lines = [ln.strip() for ln in tac_text.splitlines() if ln.strip()]
    functions: Dict[str, Tuple[List[str], List[str]]] = {}
    globals_env: Dict[str, object] = {}

    idx = 0
    while idx < len(lines):
        ln = lines[idx]
        m_fn = re.match(r"^func\s+(?:(?:int|float|char|bool|void)\s+)?([A-Za-z_][A-Za-z0-9_]*)(?:\(([^)]*)\))?:?$", ln)
        if m_fn:
            fn_name = m_fn.group(1)
            inline_params = [
                p.strip() for p in (m_fn.group(2) or "").split(",") if p.strip()
            ]
            body: List[str] = []
            params = list(inline_params)
            idx += 1
            while idx < len(lines) and lines[idx] != "endfunc":
                b_ln = lines[idx]
                m_p = re.match(
                    r"^param\s+(?:int|float|char|bool)(?:\[\])?\s+([A-Za-z_][A-Za-z0-9_$#]*)$",
                    b_ln,
                )
                if m_p:
                    params.append(m_p.group(1))
                else:
                    body.append(b_ln)
                idx += 1
            functions[fn_name] = (params, body)
        idx += 1

    prints: List[str] = []

    def run_func(fn_name: str, args: List[object], depth: int = 0) -> object:
        if depth > 200 or fn_name not in functions:
            return 0
        params, body = functions[fn_name]
        env: Dict[str, object] = dict(globals_env)
        arrays: Dict[str, Dict[int, object]] = {}
        for p_name, p_val in zip(params, args):
            env[p_name] = p_val

        labels: Dict[str, int] = {}
        for i, inst in enumerate(body):
            if inst.endswith(":") and not inst.startswith("func "):
                labels[inst[:-1].strip()] = i

        pending_args: List[object] = []
        pc = 0
        steps = 0
        while 0 <= pc < len(body) and steps < 10000:
            steps += 1
            inst = body[pc]
            if inst.endswith(":") or inst.startswith("local ") or inst == "param":
                pc += 1
                continue

            if inst.startswith("arg ") or inst.startswith("param "):
                opnd = inst.split(None, 1)[1].strip()
                pending_args.append(_eval_sim_val(opnd, env))
                pc += 1
                continue

            if inst.startswith("print "):
                opnd = inst[len("print ") :].strip()
                val = _eval_sim_val(opnd, env)
                if isinstance(val, bool):
                    prints.append("true" if val else "false")
                else:
                    prints.append(str(val))
                pc += 1
                continue

            if inst == "return" or inst.startswith("return "):
                if inst == "return":
                    return None
                opnd = inst[len("return ") :].strip()
                return _eval_sim_val(opnd, env)

            if inst.startswith("goto "):
                target = inst[len("goto ") :].strip()
                pc = labels[target]
                continue

            m_iff = re.match(r"^(?:if_false|ifFalse)\s+(\S+)\s+goto\s+(\S+)$", inst)
            if m_iff:
                cond_val = _eval_sim_val(m_iff.group(1), env)
                if not bool(cond_val):
                    pc = labels[m_iff.group(2)]
                else:
                    pc += 1
                continue

            m_store_fn = re.match(r"^store\s+([A-Za-z_][A-Za-z0-9_$#]*)\[(.+)\],\s*(.+)$", inst)
            if m_store_fn:
                arr, ix_s, val_s = m_store_fn.groups()
                ix = int(_eval_sim_val(ix_s, env))  # type: ignore[arg-type]
                arrays.setdefault(arr, {})[ix] = _eval_sim_val(val_s, env)
                pc += 1
                continue

            m_arr_st = re.match(r"^([A-Za-z_][A-Za-z0-9_$#]*)\[(.+)\]\s*=\s*(.+)$", inst)
            if m_arr_st:
                arr, ix_s, val_s = m_arr_st.groups()
                ix = int(_eval_sim_val(ix_s, env))  # type: ignore[arg-type]
                arrays.setdefault(arr, {})[ix] = _eval_sim_val(val_s, env)
                pc += 1
                continue

            m_call_void = re.match(r"^call\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+)$", inst)
            if m_call_void:
                callee, n_str = m_call_void.groups()
                n_args = int(n_str)
                call_args = pending_args[-n_args:] if n_args > 0 else []
                if n_args > 0:
                    pending_args = pending_args[:-n_args]
                else:
                    pending_args.clear()
                run_func(callee, call_args, depth + 1)
                pc += 1
                continue

            if "=" in inst:
                lhs, rhs = [p.strip() for p in inst.split("=", 1)]
                m_call = re.match(r"^call\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+)$", rhs)
                if m_call:
                    callee, n_str = m_call.groups()
                    n_args = int(n_str)
                    call_args = pending_args[-n_args:] if n_args > 0 else []
                    if n_args > 0:
                        pending_args = pending_args[:-n_args]
                    else:
                        pending_args.clear()
                    env[lhs] = run_func(callee, call_args, depth + 1)
                    pc += 1
                    continue

                m_load = re.match(r"^(?:load\s+)?([A-Za-z_][A-Za-z0-9_$#]*)\[(.+)\]$", rhs)
                if m_load:
                    arr, ix_s = m_load.groups()
                    ix = int(_eval_sim_val(ix_s, env))  # type: ignore[arg-type]
                    env[lhs] = arrays.get(arr, {}).get(ix, 0)
                    pc += 1
                    continue

                m_un = re.match(r"^(not|!|-|int2float)\s+(\S+)$", rhs)
                if m_un:
                    op, opnd = m_un.groups()
                    v = _eval_sim_val(opnd, env)
                    if op in ("not", "!"):
                        env[lhs] = not bool(v)
                    elif op == "-":
                        env[lhs] = -v  # type: ignore[operator]
                    elif op == "int2float":
                        env[lhs] = float(v)  # type: ignore[arg-type]
                    pc += 1
                    continue

                m_bin = re.match(
                    r"^(\S+)\s+(\+|-|\*|/|%|<=|>=|<|>|==|!=|&&|\|\||and|or)\s+(\S+)$",
                    rhs,
                )
                if m_bin:
                    a_s, op, b_s = m_bin.groups()
                    a = _eval_sim_val(a_s, env)
                    b = _eval_sim_val(b_s, env)
                    if op == "+":
                        env[lhs] = a + b  # type: ignore[operator]
                    elif op == "-":
                        env[lhs] = a - b  # type: ignore[operator]
                    elif op == "*":
                        env[lhs] = a * b  # type: ignore[operator]
                    elif op == "/":
                        env[lhs] = int(a / b) if isinstance(a, int) and isinstance(b, int) else a / b  # type: ignore[operator]
                    elif op == "%":
                        env[lhs] = a % b  # type: ignore[operator]
                    elif op == "<":
                        env[lhs] = a < b  # type: ignore[operator]
                    elif op == "<=":
                        env[lhs] = a <= b  # type: ignore[operator]
                    elif op == ">":
                        env[lhs] = a > b  # type: ignore[operator]
                    elif op == ">=":
                        env[lhs] = a >= b  # type: ignore[operator]
                    elif op == "==":
                        env[lhs] = a == b
                    elif op == "!=":
                        env[lhs] = a != b
                    elif op in ("&&", "and"):
                        env[lhs] = bool(a) and bool(b)
                    elif op in ("||", "or"):
                        env[lhs] = bool(a) or bool(b)
                    pc += 1
                    continue

                env[lhs] = _eval_sim_val(rhs, env)
            pc += 1
        return None

    ret = run_func("main", []) if "main" in functions else None
    return SimResult(prints=prints, return_value=str(ret) if ret is not None else None)


def extract_reference_ir(txt_content: str, prefer_optimized: bool) -> str:
    """Extrai o bloco de IR de referência ou otimizado de um arquivo .txt da suíte."""
    lines = txt_content.splitlines()
    collecting = False
    collected: List[str] = []

    target_headers = (
        ("IR otimizada esperada", "IR otimizada possível")
        if prefer_optimized
        else ("IR canônica esperada", "IR de referência")
    )

    for ln in lines:
        stripped = ln.strip()
        if any(stripped.startswith(h) for h in target_headers):
            collecting = True
            collected.clear()
            continue
        if collecting:
            if stripped.startswith(
                ("Observação:", "Verificar:", "Critério:", "IR otimizada")
            ):
                break
            if stripped:
                collected.append(ln)

    if collected and not any(l.strip().startswith("func ") for l in collected):
        collected = ["func main"] + collected + ["endfunc"]
    return "\n".join(collected)


def normalize_tac_structure(tac_text: str) -> List[str]:
    """Normaliza temporários, rótulos e variações sintáticas canônicas de TAC."""
    raw_lines = [ln.strip() for ln in tac_text.splitlines() if ln.strip()]
    filtered: List[str] = []
    for ln in raw_lines:
        if ln.startswith("local ") or ln == "param":
            continue
        if re.match(r"^param\s+(?:int|float|char|bool)(?:\[\])?\s+\S+$", ln):
            continue
        m_fn = re.match(
            r"^func\s+(?:(?:int|float|char|bool|void)\s+)?([A-Za-z_][A-Za-z0-9_]*)(?:\([^)]*\))?:?$",
            ln,
        )
        if m_fn:
            filtered.append(f"func {m_fn.group(1)}")
            continue
        if ln.startswith("param "):
            filtered.append("arg " + ln[len("param ") :].strip())
            continue
        ln = re.sub(r"^ifFalse\b", "if_false", ln)
        ln = re.sub(r"=\s*not\s+", "= ! ", ln)
        ln = re.sub(r"\band\b", "&&", ln)
        ln = re.sub(r"\bor\b", "||", ln)
        filtered.append(ln)

    # 1. Remove dead goto immediately after return
    step1: List[str] = []
    for idx, ln in enumerate(filtered):
        if (
            ln.startswith("goto ")
            and step1
            and (step1[-1] == "return" or step1[-1].startswith("return "))
        ):
            continue
        step1.append(ln)

    # 2. Remove labels not targeted by any goto / if_false
    targeted_labels = set()
    for ln in step1:
        m_g = re.search(r"\bgoto\s+(\S+)$", ln)
        if m_g:
            targeted_labels.add(m_g.group(1))
    step2 = [
        ln
        for ln in step1
        if not (ln.endswith(":") and not ln.startswith("func ") and ln[:-1].strip() not in targeted_labels)
    ]

    # 3. Sort adjacent independent constant assignments at the start of a function
    step3: List[str] = []
    idx = 0
    while idx < len(step2):
        if step2[idx].startswith("func "):
            step3.append(step2[idx])
            idx += 1
            const_inits: List[str] = []
            while idx < len(step2) and re.match(
                r"^[A-Za-z_][A-Za-z0-9_$#]*\s*=\s*(?:-?[0-9]+(?:\.[0-9]+)?|true|false)$",
                step2[idx],
            ):
                const_inits.append(step2[idx])
                idx += 1
            step3.extend(sorted(const_inits))
        else:
            step3.append(step2[idx])
            idx += 1
    filtered = step3

    # Canonicalize temporary names (t1, t2, ...), label names (L1, L2, ...), and shadowed vars
    temp_map: Dict[str, str] = {}
    label_map: Dict[str, str] = {}
    shadow_map: Dict[str, str] = {}

    def map_token(tok: str) -> str:
        if re.match(r"^t[0-9]+$", tok):
            if tok not in temp_map:
                temp_map[tok] = f"T{len(temp_map) + 1}"
            return temp_map[tok]
        if re.match(r"^L[A-Za-z0-9_]*$", tok):
            if tok not in label_map:
                label_map[tok] = f"LBL{len(label_map) + 1}"
            return label_map[tok]
        if "$" in tok or "#" in tok:
            base = re.split(r"[$#]", tok, 1)[0]
            if tok not in shadow_map:
                shadow_map[tok] = f"{base}@S{len(shadow_map) + 1}"
            return shadow_map[tok]
        return tok

    norm_lines: List[str] = []
    for ln in filtered:
        if ln.startswith("func "):
            temp_map.clear()
            label_map.clear()
            shadow_map.clear()
            norm_lines.append(ln)
            continue
        if ln.endswith(":"):
            lbl = ln[:-1].strip()
            norm_lines.append(f"{map_token(lbl)}:")
            continue
        tokens = re.split(r"(\s+|\[|\]|,)", ln)
        norm_lines.append("".join(map_token(t) if t.strip() else t for t in tokens))

    return norm_lines


def expected_error_exit_code(txt_content: str) -> int:
    m = re.search(r"código de saída\s+([0-9]+)", txt_content, re.IGNORECASE)
    if m:
        return int(m.group(1))
    lower = txt_content.lower()
    if "léxico" in lower or "lexico" in lower:
        return 2
    if "sintático" in lower or "sintatico" in lower:
        return 3
    return 4


def verify_case(
    cmd_base: List[str],
    c_file: Path,
    txt_file: Path,
    category: str,
    env: Dict[str, str],
) -> Tuple[bool, str]:
    txt_content = txt_file.read_text(encoding="utf-8")

    if category == "erros":
        exp_code = expected_error_exit_code(txt_content)
        proc = subprocess.run(
            cmd_base + ["--ir", str(c_file)],
            cwd=ROOT,
            env=env,
            capture_output=True,
        )
        out_str = (
            proc.stdout.decode("utf-8", errors="replace")
            + proc.stderr.decode("utf-8", errors="replace")
        ).strip()
        if proc.returncode == 0:
            return False, "o compilador aceitou um caso que deveria apresentar erro"
        if proc.returncode != exp_code:
            return (
                False,
                f"código de saída {proc.returncode} diferente da categoria esperada ({exp_code})",
            )
        if not out_str:
            return False, "nenhum diagnóstico emitido para o erro"
        if "func " in out_str or "endfunc" in out_str:
            return False, "IR emitida indevidamente para programa inválido"
        return True, f"rejeitado com código {proc.returncode}"

    if category == "normais":
        proc = subprocess.run(
            cmd_base + ["--ir", str(c_file)],
            cwd=ROOT,
            env=env,
            capture_output=True,
        )
        if proc.returncode != 0:
            return False, f"o compilador retornou código de saída {proc.returncode}"
        actual_ir = proc.stdout.decode("utf-8", errors="replace").strip()
        ref_ir = extract_reference_ir(txt_content, prefer_optimized=False)

        sim_actual = simulate_tac(actual_ir)
        sim_ref = simulate_tac(ref_ir)
        if sim_actual != sim_ref:
            return (
                False,
                f"efeito observável divergente: obtido={sim_actual}, esperado={sim_ref}",
            )

        # For P01..P10 (except P07 which explicitly allows direct array indexing vs scaled load/store,
        # and P09 where outer x is un-suffixed x and inner x is x$2), check normalized structure
        if c_file.stem not in ("P07", "P09"):
            norm_actual = normalize_tac_structure(actual_ir)
            norm_ref = normalize_tac_structure(ref_ir)
            if norm_actual != norm_ref:
                return (
                    False,
                    f"estrutura TAC divergente:\nobtido:   {norm_actual}\nesperado: {norm_ref}",
                )
        elif c_file.stem == "P07":
            if "v[i] = 12" not in actual_ir or "= v[i]" not in actual_ir:
                return False, "operações indexadas em vetor ausentes em P07"
        elif c_file.stem == "P09":
            if "x$2 = 8" not in actual_ir or "print x$2" not in actual_ir:
                return False, "desambiguação de sombreamento léxico ausente em P09"

        return True, "IR canônica e semântica validadas"

    if category == "otimizacao":
        proc_o0 = subprocess.run(
            cmd_base + ["-O0", "--ir", str(c_file)],
            cwd=ROOT,
            env=env,
            capture_output=True,
        )
        proc_o1 = subprocess.run(
            cmd_base + ["-O1", "--ir", str(c_file)],
            cwd=ROOT,
            env=env,
            capture_output=True,
        )
        if proc_o0.returncode != 0:
            return False, f"falha em -O0 (código {proc_o0.returncode})"
        if proc_o1.returncode != 0:
            return False, f"falha em -O1 (código {proc_o1.returncode})"

        ir_o0 = proc_o0.stdout.decode("utf-8", errors="replace").strip()
        ir_o1 = proc_o1.stdout.decode("utf-8", errors="replace").strip()
        ref_o1 = extract_reference_ir(txt_content, prefer_optimized=True)

        sim_o0 = simulate_tac(ir_o0)
        sim_o1 = simulate_tac(ir_o1)
        sim_ref = simulate_tac(ref_o1)

        if sim_o0 != sim_o1:
            return (
                False,
                f"divergência semântica entre -O0 ({sim_o0}) e -O1 ({sim_o1})",
            )
        if sim_o1 != sim_ref:
            return (
                False,
                f"divergência semântica contra gabarito: obtido={sim_o1}, esperado={sim_ref}",
            )

        if c_file.stem != "O09":
            norm_o1 = normalize_tac_structure(ir_o1)
            norm_ref = normalize_tac_structure(ref_o1)
            if norm_o1 != norm_ref:
                return (
                    False,
                    f"transformação -O1 divergente do alvo:\nobtido:   {norm_o1}\nesperado: {norm_ref}",
                )
        else:
            # O09: verify strength reduction eliminated multiplication inside the loop
            if "*" in ir_o1:
                return False, "multiplicação não foi reduzida no laço em O09"

        return True, "IR otimizada (-O1) e equivalência validadas"

    return False, f"categoria desconhecida: {category}"


def classify_case(rel_path: str) -> str:
    lower = rel_path.lower()
    if "01-" in lower:
        return "normais"
    if "02-" in lower:
        return "erros"
    if "03-" in lower:
        return "otimizacao"
    raise ValueError(f"Categoria não identificada para {rel_path}")


def run_suite_for_target(
    label: str, cmd_base: List[str], suite_dir: Path, env: Dict[str, str]
) -> bool:
    totals = {"normais": 0, "erros": 0, "otimizacao": 0}
    passed = {"normais": 0, "erros": 0, "otimizacao": 0}

    c_files = sorted(suite_dir.rglob("*.c"))
    if not c_files:
        print(f"Erro: nenhum arquivo .c foi encontrado em {suite_dir}", file=sys.stderr)
        return False

    for c_file in c_files:
        rel = str(c_file.relative_to(suite_dir))
        cat = classify_case(rel)
        totals[cat] += 1
        txt_file = c_file.with_suffix(".txt")
        if not txt_file.is_file():
            print(f"[FALHA][{cat}] {c_file.name} — gabarito não encontrado")
            continue

        ok, reason = verify_case(cmd_base, c_file, txt_file, cat, env)
        if ok:
            passed[cat] += 1
            print(f"[OK][{cat}] {c_file.name}")
        else:
            print(f"[FALHA][{cat}] {c_file.name} — {reason}")

    print("\nResumo:")
    print(f"  Testes normais:      {passed['normais']}/{totals['normais']} aprovados")
    print(f"  Testes com erro:     {passed['erros']}/{totals['erros']} aprovados")
    print(f"  Testes otimização:   {passed['otimizacao']}/{totals['otimizacao']} aprovados")

    return passed == totals


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Executor e validador da suíte de 30 casos de IR e Otimização."
    )
    parser.add_argument(
        "suite",
        nargs="?",
        default="minic-ir-test-cases",
        help="Diretório da suíte minic-ir-test-cases",
    )
    parser.add_argument("--python", dest="python_script", help="Caminho para minic.py")
    parser.add_argument("--c", dest="c_source", help="Caminho para minic.c")
    parser.add_argument("--bin", dest="binary", help="Caminho para executável C já compilado")
    args = parser.parse_args(argv)

    suite_dir = Path(args.suite)
    if not suite_dir.is_dir():
        print(f"Erro: diretório de testes não encontrado: {suite_dir}", file=sys.stderr)
        return 2

    gcc = find_gcc()
    env = os.environ.copy()
    gcc_dir = str(Path(gcc).resolve().parent)
    if Path(gcc_dir).is_dir():
        env["PATH"] = gcc_dir + os.pathsep + env.get("PATH", "")

    if args.python_script:
        py_path = Path(args.python_script)
        if not py_path.is_file():
            print(f"Erro: não encontrei o compilador: {py_path}", file=sys.stderr)
            return 2
        ok = run_suite_for_target("Python", [sys.executable, str(py_path)], suite_dir, env)
        return 0 if ok else 1

    if args.binary:
        bin_path = Path(args.binary)
        if not bin_path.is_file():
            print(f"Erro: executável não encontrado: {bin_path}", file=sys.stderr)
            return 2
        ok = run_suite_for_target("C", [str(bin_path)], suite_dir, env)
        return 0 if ok else 1

    if args.c_source:
        c_src = Path(args.c_source)
        if not c_src.is_file():
            print(f"Erro: fonte C não encontrada: {c_src}", file=sys.stderr)
            return 2
        with tempfile.TemporaryDirectory() as tmp:
            ext = ".exe" if os.name == "nt" else ""
            out_bin = str(Path(tmp) / f"minic{ext}")
            subprocess.run(
                [gcc, "-std=c11", "-Wall", "-Wextra", "-pedantic", "-O2", str(c_src), "-o", out_bin],
                cwd=ROOT,
                env=env,
                check=True,
            )
            ok = run_suite_for_target("C", [out_bin], suite_dir, env)
            return 0 if ok else 1

    # Default: run both Python and C and verify parity
    print("=== Avaliando Compilador Python (minic.py) ===")
    ok_py = run_suite_for_target("Python", [sys.executable, str(ROOT / "minic.py")], suite_dir, env)

    print("\n=== Avaliando Compilador C (minic.c) ===")
    with tempfile.TemporaryDirectory() as tmp:
        ext = ".exe" if os.name == "nt" else ""
        out_bin = str(Path(tmp) / f"minic{ext}")
        subprocess.run(
            [gcc, "-std=c11", "-Wall", "-Wextra", "-pedantic", "-O2", str(ROOT / "minic.c"), "-o", out_bin],
            cwd=ROOT,
            env=env,
            check=True,
        )
        ok_c = run_suite_for_target("C", [out_bin], suite_dir, env)

    return 0 if (ok_py and ok_c) else 1


if __name__ == "__main__":
    sys.exit(main())
