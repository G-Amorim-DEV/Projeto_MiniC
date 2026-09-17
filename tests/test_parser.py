"""Regression and grammar-boundary tests shared by both MiniC parsers."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from ProjetoMiniC.src.parser.__main__ import analisar_fonte


ROOT = Path(__file__).resolve().parents[1]


VALID_CASES = {
    "empty function": "void main() {}",
    "global declarator list": "int a, b[2], c = 3;",
    "local declarator list": "int main() { int a = 1, b[2]; return a; }",
    "parameters": "float mean(int values[], int count) { return values[0]; }",
    "if else": "int main() { if (true) return 1; else return 0; }",
    "dangling else": "int main() { if (true) if (false) return 1; else return 2; }",
    "loops": "void f() { while (true) break; for (;; ) continue; }",
    "io": "void f() { int a[2]; read(a[0]); print(\"ok\"); }",
    "calls": "int f(int x) { return x; } int main() { return f(1); }",
    "precedence": "int main() { return 1 + 2 * 3 < 8 == true || false && true; }",
    "right associative assignment": "void f() { int a, b; a = b = 1; }",
    "unary and grouping": "int f() { return !(-1 + 2); }",
}

INVALID_CASES = {
    "void variable": "void value;",
    "missing type": "main() {}",
    "missing identifier": "int () {}",
    "trailing parameter comma": "int f(int x,) {}",
    "sized array parameter": "int f(int a[2]) {}",
    "missing expression": "int f() { return 1 + ; }",
    "invalid assignment target": "int f() { (1 + 2) = 3; }",
    "invalid read target": "void f() { read(1); }",
    "orphan else": "void f() { else return; }",
    "missing closing block": "void f() { return;",
}


class ParserCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "parser"], cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def run_parser(self, command, source):
        with tempfile.NamedTemporaryFile("w", suffix=".minic", encoding="utf-8") as stream:
            stream.write(source)
            stream.flush()
            return subprocess.run(command + [stream.name], cwd=ROOT, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_valid_grammar_is_accepted_by_both_parsers(self):
        for name, source in VALID_CASES.items():
            with self.subTest(name=name):
                python = self.run_parser(["python3", "parser.py"], source)
                native = self.run_parser(["./parser"], source)
                self.assertEqual(0, python.returncode, python.stderr)
                self.assertEqual(0, native.returncode, native.stderr)
                self.assertTrue(python.stdout.startswith("Program("))
                self.assertTrue(native.stdout.startswith("Program("))

    def test_invalid_syntax_is_rejected(self):
        for name, source in INVALID_CASES.items():
            with self.subTest(name=name):
                for command in (["python3", "parser.py"], ["./parser"]):
                    result = self.run_parser(command, source)
                    self.assertEqual(3, result.returncode,
                                     "{} accepted by {}: {}".format(name, command, result.stdout))
                    self.assertIn("linha", result.stderr)
                    self.assertIn("coluna", result.stderr)

    def test_lexical_error_exit_code(self):
        for command in (["python3", "parser.py"], ["./parser"]):
            result = self.run_parser(command, "int main() { return @; }")
            self.assertEqual(2, result.returncode)

    def test_assignment_ast_is_right_associative(self):
        result = self.run_parser(["python3", "parser.py"], "void f() { int a, b; a = b = 1; }")
        expected = ("Program(Function(void f() Block(VarDecl(int a), VarDecl(int b), "
                    "ExprStmt(Assign(Id(a),Assign(Id(b),Lit(int,1)))))))\n")
        self.assertEqual(expected, result.stdout)

    def test_ui_analysis_reports_ast_and_errors(self):
        valido = analisar_fonte("int main() { return 0; }")
        self.assertTrue(valido.sucesso)
        self.assertEqual("Program(Function(int main() Block(Return(Lit(int,0)))))", valido.ast)
        self.assertIn("Programa", valido.arvore_descendente)
        self.assertFalse(valido.diagnosticos)
        self.assertTrue(valido.tokens)

        sintatico = analisar_fonte("int main( { return 0; }")
        self.assertEqual(3, sintatico.codigo_saida)
        self.assertTrue(sintatico.diagnosticos)
        self.assertIn("linha", sintatico.diagnosticos[0])

        lexico = analisar_fonte("int main() { @ }")
        self.assertEqual(2, lexico.codigo_saida)
        self.assertTrue(lexico.diagnosticos[0].startswith("[ERRO LÉXICO]"))


if __name__ == "__main__":
    unittest.main()
