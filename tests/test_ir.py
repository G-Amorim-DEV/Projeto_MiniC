"""Suíte de testes da etapa de Representação Intermediária (IR / TAC) em Python e C."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ProjetoMiniC.src.ast.nodes import Break, Lit, Program, Return
from ProjetoMiniC.src.ir import (
    IRGenerationError,
    IRGenerator,
    format_ir,
    generate_ir,
)
from ProjetoMiniC.src.ir.__main__ import analisar_ir
from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.optimizer import optimize_ir
from ProjetoMiniC.src.parser import Parser
from ProjetoMiniC.src.semantic import SemanticAnalyzer
import test_ir_30

ROOT = Path(__file__).resolve().parents[1]


def _find_gcc() -> str:
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


def compile_to_ir_python(source: str, optimize: bool = False) -> str:
    scanner = Scanner(source)
    scanner.scan_tokens()
    assert not scanner.errors, scanner.errors
    parser = Parser(scanner.tokens, semantic_mode=True)
    tree = parser.parse()
    assert tree is not None, parser.errors
    diagnostics = SemanticAnalyzer().analyze(tree)
    assert not diagnostics, diagnostics
    ir_prog = generate_ir(tree)
    if optimize:
        ir_prog = optimize_ir(ir_prog)
    return format_ir(ir_prog)


class IRGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.gcc = _find_gcc()
        cls.env = os.environ.copy()
        gcc_dir = str(Path(cls.gcc).resolve().parent)
        cls.env["PATH"] = gcc_dir + os.pathsep + cls.env.get("PATH", "")
        cls.env["PYTHONIOENCODING"] = "utf-8"

        ext = ".exe" if os.name == "nt" else ""
        cls.minic_bin = str(Path(cls.temp_dir.name) / f"minic{ext}")
        cls.ir_bin = str(Path(cls.temp_dir.name) / f"ir{ext}")
        cls.api_check_bin = str(Path(cls.temp_dir.name) / f"ir_api_check{ext}")

        for src, out in (
            ("minic.c", cls.minic_bin),
            ("ir.c", cls.ir_bin),
            ("tests/ir_api_check.c", cls.api_check_bin),
        ):
            subprocess.run(
                [
                    cls.gcc,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-pedantic",
                    "-Werror",
                    "-O2",
                    src,
                    "-o",
                    out,
                ],
                cwd=ROOT,
                env=cls.env,
                check=True,
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def run_cli(self, command: list[str], source: str) -> subprocess.CompletedProcess[str]:
        fd, temp_path = tempfile.mkstemp(suffix=".c", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(source)
            return subprocess.run(
                command + [temp_path],
                cwd=ROOT,
                env=self.env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def assert_ir_matches(self, source: str, expected_tac: str) -> None:
        py_tac = compile_to_ir_python(source)
        self.assertEqual(expected_tac.strip(), py_tac.strip())

        py_cli = self.run_cli([sys.executable, "minic.py", "--ir"], source)
        c_cli = self.run_cli([self.minic_bin, "--ir"], source)
        ir_py_cli = self.run_cli([sys.executable, "ir.py"], source)
        ir_c_cli = self.run_cli([self.ir_bin], source)
        main_py_cli = self.run_cli([sys.executable, "main.py", "--ir"], source)

        for proc in (py_cli, c_cli, ir_py_cli, ir_c_cli, main_py_cli):
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertEqual("", proc.stderr)
            self.assertEqual(expected_tac.strip(), proc.stdout.strip())

    def test_precedence_and_associativity_and_unary(self) -> None:
        source = """
        int main() {
            int a = 1, b = 2, c = 3, x;
            bool ok;
            x = a + b * c - -a;
            ok = !(x > 5 && b <= c || a == 0);
            return x;
        }
        """
        expected = """
func int main:
  local int a
  a = 1
  local int b
  b = 2
  local int c
  c = 3
  local int x
  local bool ok
  t1 = b * c
  t2 = a + t1
  t3 = - a
  t4 = t2 - t3
  x = t4
  t5 = x > 5
  t6 = b <= c
  t7 = t5 && t6
  t8 = a == 0
  t9 = t7 || t8
  t10 = ! t9
  ok = t10
  return x
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_int_to_float_coercions_and_chained_assignments(self) -> None:
        source = """
        float g = 1;
        float promove(float p) {
            float loc = 2;
            loc = 3;
            return 4;
        }
        int main() {
            int a, b;
            float c, r;
            c = a = b = 5;
            r = promove(a) + 2;
            return a;
        }
        """
        expected = """
global float g
t1 = int2float 1
g = t1
func float promove:
  param float p
  local float loc
  t2 = int2float 2
  loc = t2
  t3 = int2float 3
  loc = t3
  t4 = int2float 4
  return t4
endfunc
func int main:
  local int a
  local int b
  local float c
  local float r
  b = 5
  a = b
  t5 = int2float a
  c = t5
  t6 = int2float a
  arg t6
  t7 = call promove, 1
  t8 = int2float 2
  t9 = t7 + t8
  r = t9
  return a
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_declarations_arrays_and_indexing(self) -> None:
        source = """
        int global_arr[4];
        int soma_par(int v[], int i) {
            return v[i] + v[i + 1];
        }
        int main() {
            int local_arr[2];
            local_arr[0] = 10;
            local_arr[1] = 20;
            global_arr[0] = soma_par(local_arr, 0);
            return global_arr[0];
        }
        """
        expected = """
global int global_arr[4]
func int soma_par:
  param int[] v
  param int i
  t1 = v[i]
  t2 = i + 1
  t3 = v[t2]
  t4 = t1 + t3
  return t4
endfunc
func int main:
  local int local_arr[2]
  local_arr[0] = 10
  local_arr[1] = 20
  arg local_arr
  arg 0
  t5 = call soma_par, 2
  global_arr[0] = t5
  t6 = global_arr[0]
  return t6
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_if_and_if_else_control_flow(self) -> None:
        source = """
        int classifica(int n) {
            int r = 0;
            if (n > 0) {
                r = 1;
            }
            if (n < 0) {
                return -1;
            } else {
                return r;
            }
        }
        """
        expected = """
func int classifica:
  param int n
  local int r
  r = 0
  t1 = n > 0
  if_false t1 goto L1
  r = 1
  L1:
  t2 = n < 0
  if_false t2 goto L2
  t3 = - 1
  return t3
  goto L3
  L2:
  return r
  L3:
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_while_for_nested_loops_break_and_continue(self) -> None:
        source = """
        int main() {
            int i = 0, j = 0, s = 0;
            while (i < 5) {
                for (j = 0; j < 4; j = j + 1) {
                    if (j == 1) continue;
                    if (j == 3) break;
                    s = s + j;
                }
                i = i + 1;
                if (i == 4) break;
                if (i == 2) continue;
            }
            return s;
        }
        """
        expected = """
func int main:
  local int i
  i = 0
  local int j
  j = 0
  local int s
  s = 0
  L1:
  t1 = i < 5
  if_false t1 goto L2
  j = 0
  L3:
  t2 = j < 4
  if_false t2 goto L5
  t3 = j == 1
  if_false t3 goto L6
  goto L4
  L6:
  t4 = j == 3
  if_false t4 goto L7
  goto L5
  L7:
  t5 = s + j
  s = t5
  L4:
  t6 = j + 1
  j = t6
  goto L3
  L5:
  t7 = i + 1
  i = t7
  t8 = i == 4
  if_false t8 goto L8
  goto L2
  L8:
  t9 = i == 2
  if_false t9 goto L9
  goto L1
  L9:
  goto L1
  L2:
  return s
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_functions_recursion_and_void_calls(self) -> None:
        source = """
        void log_num(int v) {
            print(v);
            return;
        }
        int fat(int n) {
            if (n <= 1) return 1;
            else return n * fat(n - 1);
        }
        int main() {
            int r = fat(5);
            log_num(r);
            return r;
        }
        """
        expected = """
func void log_num:
  param int v
  print v
  return
endfunc
func int fat:
  param int n
  t1 = n <= 1
  if_false t1 goto L1
  return 1
  goto L2
  L1:
  t2 = n - 1
  arg t2
  t3 = call fat, 1
  t4 = n * t3
  return t4
  L2:
endfunc
func int main:
  local int r
  arg 5
  t5 = call fat, 1
  r = t5
  arg r
  call log_num, 1
  return r
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_lexical_scoping_and_shadowing_disambiguation(self) -> None:
        source = """
        int x = 100;
        int f(int x) {
            int y = x;
            {
                int x = 20;
                int y = 30;
                y = x + y;
            }
            {
                int x = 40;
                y = y + x;
            }
            return x + y;
        }
        """
        expected = """
global int x
x = 100
func int f:
  param int x$1
  local int y
  y = x$1
  local int x$2
  x$2 = 20
  local int y$2
  y$2 = 30
  t1 = x$2 + y$2
  y$2 = t1
  local int x$3
  x$3 = 40
  t2 = y + x$3
  y = t2
  t3 = x$1 + y
  return t3
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_read_and_print_scalars_arrays_and_literals(self) -> None:
        source = """
        void io_demo() {
            int a;
            int v[3];
            char c = 'A';
            read(a);
            read(v[a]);
            print(v[a]);
            print(c);
            print("fim");
        }
        """
        expected = """
func void io_demo:
  local int a
  local int v[3]
  local char c
  c = 'A'
  read a
  read v[a]
  t1 = v[a]
  print t1
  print c
  print "fim"
endfunc
"""
        self.assert_ir_matches(source, expected)

    def test_errors_block_ir_generation_in_python_and_c(self) -> None:
        cases = [
            ("lexical error", "int main() { return @; }", 2),
            ("syntax error", "int main( { return 0; }", 3),
            ("semantic error", "int main() { int x = 2.5; return ausente; }", 4),
        ]
        for label, source, expected_code in cases:
            with self.subTest(label=label):
                for cmd in (
                    [sys.executable, "minic.py", "--ir"],
                    [self.minic_bin, "--ir"],
                    [sys.executable, "ir.py"],
                    [self.ir_bin],
                    [sys.executable, "main.py", "--ir"],
                ):
                    res = self.run_cli(cmd, source)
                    self.assertEqual(expected_code, res.returncode)
                    self.assertNotIn("func ", res.stdout)
                    self.assertNotIn("endfunc", res.stdout)

    def test_invalid_or_unannotated_ast_rejected_by_api(self) -> None:
        # 1. Non-Program node
        with self.assertRaises(IRGenerationError):
            generate_ir(None)  # type: ignore[arg-type]

        # 2. Empty Program
        with self.assertRaises(IRGenerationError):
            generate_ir(Program([]))

        # 3. Unannotated AST (parsed without SemanticAnalyzer)
        scanner = Scanner("int main() { int a = 1; return a; }")
        scanner.scan_tokens()
        unannotated_tree = Parser(scanner.tokens, semantic_mode=True).parse()
        assert unannotated_tree is not None
        with self.assertRaises(IRGenerationError):
            generate_ir(unannotated_tree)

        # 4. AST with semantic errors
        scanner_err = Scanner("int main() { int a = 2.5; return nao_existe; }")
        scanner_err.scan_tokens()
        err_tree = Parser(scanner_err.tokens, semantic_mode=True).parse()
        assert err_tree is not None
        diags = SemanticAnalyzer().analyze(err_tree)
        self.assertTrue(diags)
        with self.assertRaises(IRGenerationError):
            generate_ir(err_tree)

        # 5. Break / Return outside valid context
        bad_break = Break()
        bad_break.semantic_type = "void"
        with self.assertRaises(IRGenerationError):
            IRGenerator().generate(Program([bad_break]))

        bad_return = Return(Lit("int", "0"))
        bad_return.semantic_type = "void"
        with self.assertRaises(IRGenerationError):
            IRGenerator().generate(Program([bad_return]))

        # 6. C API validation binary check
        c_api_res = subprocess.run(
            [self.api_check_bin], cwd=ROOT, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(0, c_api_res.returncode, c_api_res.stderr)

    def test_python_and_c_parity_across_all_valid_suites(self) -> None:
        # All 10 valid semantic test cases
        sem_cases = sorted((ROOT / "minic-testes-semanticos").glob("*.c"))[:10]
        self.assertEqual(10, len(sem_cases))
        for path in sem_cases:
            with self.subTest(suite="semantic", file=path.name):
                py_res = subprocess.run(
                    [sys.executable, "minic.py", "--ir", str(path)],
                    cwd=ROOT,
                    env=self.env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                c_res = subprocess.run(
                    [self.minic_bin, "--ir", str(path)],
                    cwd=ROOT,
                    env=self.env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(0, py_res.returncode, py_res.stderr)
                self.assertEqual(0, c_res.returncode, c_res.stderr)
                self.assertTrue(py_res.stdout.strip())
                self.assertEqual(py_res.stdout, c_res.stdout)

        # All 25 valid parser test cases that also pass semantic analysis
        parser_cases_dir = ROOT / "testes-parser-50" / "testes-parser-50" / "casos"
        if parser_cases_dir.is_dir():
            for case_dir in sorted(parser_cases_dir.iterdir()):
                if not case_dir.is_dir():
                    continue
                case_num = int(case_dir.name.split("_", 1)[0])
                if case_num > 25:
                    continue
                code_path = case_dir / "codigo.c"
                with self.subTest(suite="parser-50", case=case_dir.name):
                    py_res = subprocess.run(
                        [sys.executable, "minic.py", "--ir", str(code_path)],
                        cwd=ROOT,
                        env=self.env,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                    c_res = subprocess.run(
                        [self.minic_bin, "--ir", str(code_path)],
                        cwd=ROOT,
                        env=self.env,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                    self.assertEqual(py_res.returncode, c_res.returncode)
                    if py_res.returncode == 0:
                        self.assertEqual(py_res.stdout, c_res.stdout)

    def test_gui_helper_analisar_ir(self) -> None:
        ok = analisar_ir("int main() { int x = 2 + 3; return x; }")
        self.assertTrue(ok.sucesso)
        self.assertEqual(0, ok.codigo_saida)
        self.assertIn("t1 = 2 + 3", ok.ir_texto)
        self.assertIsNotNone(ok.ir_program)

        err_sem = analisar_ir("int main() { int x = 2.5; return x; }")
        self.assertFalse(err_sem.sucesso)
        self.assertEqual(4, err_sem.codigo_saida)
        self.assertEqual("", err_sem.ir_texto)
        self.assertTrue(any("SEM003" in d for d in err_sem.diagnosticos))

        err_sin = analisar_ir("int main( { return 0; }")
        self.assertFalse(err_sin.sucesso)
        self.assertEqual(3, err_sin.codigo_saida)
        self.assertEqual("", err_sin.ir_texto)

        err_lex = analisar_ir("int main() { @ }")
        self.assertFalse(err_lex.sucesso)
        self.assertEqual(2, err_lex.codigo_saida)
        self.assertEqual("", err_lex.ir_texto)

    def test_temp_and_label_collision_avoidance(self) -> None:
        # Caso 1: exemplo exato da Fase 2.1 (global t1 = 9)
        source_global_t1 = """
        int t1 = 9;
        int main() {
            int x;
            x = 2 + 3;
            return t1;
        }
        """
        expected_global_t1 = """
global int t1
t1 = 9
func int main:
  local int x
  t2 = 2 + 3
  x = t2
  return t1
endfunc
"""
        self.assert_ir_matches(source_global_t1, expected_global_t1)

        # Caso 2: colisões múltiplas com parâmetros, locais em sub-blocos e nomes de rótulos (L1)
        source_multi = """
        int t1 = 9;
        int soma_t(int t2) {
            int t3 = 4;
            int L1 = 1;
            {
                int t4 = 5;
                if (L1 > 0) {
                    t3 = t1 + t2 + t4;
                }
            }
            return t3;
        }
        int main() {
            return soma_t(10);
        }
        """
        expected_multi = """
global int t1
t1 = 9
func int soma_t:
  param int t2
  local int t3
  t3 = 4
  local int L1
  L1 = 1
  local int t4
  t4 = 5
  t5 = L1 > 0
  if_false t5 goto L2
  t6 = t1 + t2
  t7 = t6 + t4
  t3 = t7
  L2:
  return t3
endfunc
func int main:
  arg 10
  t8 = call soma_t, 1
  return t8
endfunc
"""
        self.assert_ir_matches(source_multi, expected_multi)

    def test_optimizer_o1_passes_and_parity(self) -> None:
        opt_dir = ROOT / "minic-ir-test-cases" / "testes" / "03-otimizacoes"
        self.assertTrue(opt_dir.is_dir())
        c_files = sorted(opt_dir.rglob("*.c"))
        self.assertEqual(10, len(c_files))

        for c_file in c_files:
            with self.subTest(case=c_file.name):
                source = c_file.read_text(encoding="utf-8")
                py_tac = compile_to_ir_python(source, optimize=True)
                py_cli = self.run_cli([sys.executable, "minic.py", "-O1", "--ir"], source)
                c_cli = self.run_cli([self.minic_bin, "-O1", "--ir"], source)
                ir_py_cli = self.run_cli([sys.executable, "ir.py", "-O1"], source)
                ir_c_cli = self.run_cli([self.ir_bin, "-O1"], source)

                for proc in (py_cli, c_cli, ir_py_cli, ir_c_cli):
                    self.assertEqual(0, proc.returncode, proc.stderr)
                    self.assertEqual(py_tac.strip(), proc.stdout.strip())

    def test_suite_30_cases_ir_and_optimization(self) -> None:
        suite_path = str(ROOT / "minic-ir-test-cases")
        rc = test_ir_30.main([suite_path])
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
