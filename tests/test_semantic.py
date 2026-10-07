"""Official byte-for-byte fixtures and extra rule/cross-language tests."""
from dataclasses import fields, is_dataclass
import subprocess
import tempfile
import unittest
from pathlib import Path

from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser import Parser
from ProjetoMiniC.src.semantic import SemanticAnalyzer
from ProjetoMiniC.src.semantic.analyzer import ERROR, expression_text
from ProjetoMiniC.src.ast.nodes import Assign, Binary, Call, Id, Index, Lit, Node, Unary

ROOT = Path(__file__).resolve().parents[1]

ACCEPTED = {
    'promotion': 'float f(float x) { return x; } float g() { float x=1; x=2; return f(3); }',
    'shadowing': 'int x; int f(int x) { { float x=2.5; } return x; }',
    'logic': 'bool f() { return (1 < 2) && !(3.0 == 4); }',
    'arrays': 'float f(float a[], int i) { return a[i]; } float g() { float a[3]; a[0]=1; return f(a,0); }',
    'nested loops': 'int f() { int i=0; while (i<3) { while (false) { break; } i=i+1; } return i; }',
    'recursion': 'int f(int n) { if (n==0) return 1; else return n*f(n-1); }',
    'forward calls': 'int f() { return g(); } int g() { return 1; }',
    'void statement': 'void f() { return; } void g() { f(); }',
    'branches': 'int f(bool b) { if(b) { return 1; } else { return 2; } }',
    'right assignment': 'int f() { int a,b; a=b=1; return a; }',
    'bool arrays': 'bool f(bool a[]) { return a[0]; } bool g() { bool a[1]; a[0]=true; return f(a); }',
    'no main': 'int answer() { return 42; }',
    'char io': "void f() { char a='x'; read(a); print(a); print(\"ok\"); }",
    'for': 'void f() { int i=0; for(i=0;i<2;i=i+1) { continue; } }',
    'runtime bounds': 'int f() { int a[1]; return a[999]; }',
    'lecture example': """int soma(int a, int b) { return a + b; }
float promove(int n) { return n; }
int principal() {
  int i; float x; bool ok;
  i = soma(2, 3);
  x = promove(i) + 0.5;
  ok = x > 2.0;
  while (ok && i < 10) {
    i = i + 1;
    if (i == 7) continue;
    if (i > 8) break;
  }
  return i;
}""",
}
REJECTED = {
    'narrowing': ('int f() { int x=2.5; return x; }', ['SEM003']),
    'undeclared': ('int f() { return n; }', ['SEM001']),
    'duplicate': ('void f() { int x; float x; }', ['SEM002']),
    'parameter duplicate': ('void f(int x) { int x; }', ['SEM002']),
    'condition': ('void f() { if(1) return; }', ['SEM005']),
    'while condition': ('void f() { while(1) {} }', ['SEM005']),
    'index': ('int f() { int a[2]; return a[1.5]; }', ['SEM006']),
    'arity': ('int f(int x) { return x; } int g() { return f(); }', ['SEM007']),
    'argument': ('int f(int x) { return x; } int g() { return f(2.5); }', ['SEM008']),
    'array argument': ('void f(float x[]) {} void g() { int a[2]; f(a); }', ['SEM008']),
    'void value': ('void f() {} int g() { return f(); }', ['SEM012']),
    'return type': ('int f() { return 2.5; }', ['SEM009']),
    'missing return': ('int f(bool b) { if(b) return 1; }', ['SEM011']),
    'loop return': ('int f() { while(true) return 1; }', ['SEM011']),
    'lvalue': ('void f() { (1+2)=3; }', ['SEM013']),
    'whole array assignment': ('void f() { int a[2],b[2]; a=b; }', ['SEM013']),
    'operator': ('bool f() { return true+1; }', ['E_OPERATOR']),
    'modulo': ('int f() { return 1.5%2; }', ['E_OPERATOR']),
    'not a function': ('void f() { int x; x(); }', ['E_CALL']),
    'not an array': ('int f() { int x; return x[0]; }', ['E_ARRAY']),
    'return empty': ('int f() { return; }', ['SEM009']),
    'void return': ('void f() { return 1; }', ['SEM009']),
    'break context': ('void f() { break; }', ['SEM010']),
    'function value': ('int f() { return 1; } int g() { return f; }', ['E_FUNCTION_VALUE']),
    'assignment as return': ('int f() { int n; return n=1; }', ['SEM003']),
    'assignment as argument': ('int f(int x) { return x; } int g() { int n; return f(n=1); }', ['SEM003']),
    'assignment as condition': ('void f() { bool b; if(b=true) {} }', ['SEM003']),
    'assignment as arithmetic': ('int f() { int n; return (n=1)+true; }', ['SEM003']),
    'cascade bad index': ('int f() { int a[2]; return a[1.5]+true; }', ['SEM006']),
    'cascade bad call': ('int f(int x) { return x; } int g() { return f(2.5)+true; }', ['SEM008']),
    'cascade bad assignment': ('int f() { int n; return (n=1.5)+true; }', ['SEM003']),
    'cascade bad target': ('int f() { return (3=1)+true; }', ['SEM013']),
    'undeclared function': ('int f() { return missing(); }', ['SEM001']),
    'short circuit checking': ('bool f() { return false && missing; }', ['SEM001']),
    'independent errors': ('void f() { if(missing<true) {} float x=true; }', ['SEM001','SEM003']),
    'continue context': ('void f() { continue; }', ['SEM010']),
    'return context': ('return 1;', ['SEM010']),
}


def analyze(source, analyzer=None):
    scanner = Scanner(source)
    scanner.scan_tokens()
    assert not scanner.errors, scanner.errors
    parser = Parser(scanner.tokens, semantic_mode=True)
    tree = parser.parse()
    assert tree is not None, parser.errors
    analyzer = analyzer or SemanticAnalyzer()
    analyzer.analyze(tree)
    return analyzer


class SemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.binary = str(Path(cls.temp.name)/'minic')
        cls.annotations = str(Path(cls.temp.name)/'annotations')
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-pedantic', '-Werror', '-O2',
                        'tests/semantic_annotations.c', '-o', cls.annotations], cwd=ROOT, check=True)
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-pedantic', '-Werror', '-O2',
                        'minic.c', '-o', cls.binary], cwd=ROOT, check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_cli(self, command, source):
        with tempfile.NamedTemporaryFile('w', suffix='.c', encoding='utf-8') as stream:
            stream.write(source)
            stream.flush()
            return subprocess.run(command+[stream.name], cwd=ROOT, capture_output=True, text=True)

    def check_case(self, source, codes):
        analyzer = analyze(source)
        self.assertEqual(codes, [d.code for d in analyzer.diagnostics])
        python = self.run_cli(['python3', 'minic.py'], source)
        native = self.run_cli([self.binary], source)
        self.assertEqual(4 if codes else 0, python.returncode, python.stderr)
        self.assertEqual(python.returncode, native.returncode, native.stderr)
        self.assertEqual('', python.stderr)
        self.assertEqual('', native.stderr)
        self.assertEqual(python.stdout, native.stdout)

    def test_official_fixtures_exact_bytes(self):
        sources = sorted((ROOT/'minic-testes-semanticos').glob('*.c'))
        self.assertEqual(20, len(sources))
        for source in sources:
            with self.subTest(source=source.name):
                expected = source.with_suffix('.gabarito').read_bytes()
                expected_status = 4 if expected.startswith(b'SEM') else 0
                outputs = []
                for command in (['python3', 'minic.py'], [self.binary]):
                    result = subprocess.run(command+[str(source)], cwd=ROOT,
                                            capture_output=True)
                    self.assertEqual(expected_status, result.returncode, result.stderr)
                    self.assertEqual(b'', result.stderr)
                    self.assertEqual(expected, result.stdout)
                    outputs.append(result.stdout)
                self.assertEqual(outputs[0], outputs[1])

    def test_accepted(self):
        for name, source in ACCEPTED.items():
            with self.subTest(name=name): self.check_case(source, [])

    def test_rejected(self):
        for name, (source, codes) in REJECTED.items():
            with self.subTest(name=name): self.check_case(source, codes)

    def test_positions_and_source_text(self):
        analyzer = analyze('int f() {\n  int x = 2.50;\n  return n;\n}')
        self.assertEqual([(2,11), (3,10)], [(d.line,d.column) for d in analyzer.diagnostics])
        self.assertIn('“2.50”', analyzer.diagnostics[0].message)
        self.assertIn('“n”', analyzer.diagnostics[1].message)
        self.check_case('int f() {\n  int x = 2.50;\n  return n;\n}', ['SEM003','SEM001'])
        self.check_case('int f() { return 1 < 2; }', ['SEM009'])
        result = self.run_cli(['python3', 'main.py'], 'void f() {}')
        # Without --semantic main.py intentionally remains a lexer CLI.
        self.assertEqual(0, result.returncode)
        with tempfile.NamedTemporaryFile('w', suffix='.c', encoding='utf-8') as stream:
            stream.write('void f() {}')
            stream.flush()
            semantic = subprocess.run(['python3', 'main.py', stream.name, '--semantic'],
                                      cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, semantic.returncode, semantic.stderr)
        self.assertEqual('Análise semântica concluída: 0 erros; programa aceito.', semantic.stdout)

    @staticmethod
    def annotated_tree(source):
        scanner = Scanner(source)
        scanner.scan_tokens()
        parser = Parser(scanner.tokens, semantic_mode=True)
        tree = parser.parse()
        assert tree is not None, parser.errors
        analyzer = SemanticAnalyzer()
        original = tree.to_sexpr()
        analyzer.analyze(tree)
        assert original == tree.to_sexpr()
        return tree, analyzer

    @staticmethod
    def walk_nodes(node):
        yield node
        if is_dataclass(node):
            for descriptor in fields(node):
                value = getattr(node, descriptor.name)
                children = value if isinstance(value, list) else [value]
                for child in children:
                    if isinstance(child, Node):
                        yield from SemanticTests.walk_nodes(child)

    def test_annotations_and_coercions_python_c(self):
        source = """float global = 1;
float promote(float p) { float local=2; local=3; return 4; }
float caller() { int v[2]; v[0]=1; float y=promote(5); return v[0]+0.5; }
void chain() { int a,b; a=b=3; float c; c=a=b=2; }
"""
        tree, analyzer = self.annotated_tree(source)
        self.assertFalse(analyzer.diagnostics)
        expressions = [n for n in self.walk_nodes(tree)
                       if isinstance(n, (Id, Lit, Unary, Binary, Assign, Call, Index))]
        self.assertTrue(all(n.semantic_type is not None for n in expressions))
        coercions = [n for n in expressions if n.coercion_type == 'float']
        self.assertEqual(6, len(coercions))  # Initializers, assignment, argument, return, operator.
        self.assertTrue(all(n.semantic_type == 'int' for n in coercions))
        assignments = [n for n in expressions if isinstance(n, Assign)]
        self.assertTrue(all(n.semantic_type == 'void' for n in assignments))
        self.assertTrue(all(n.coercion_type is None for n in assignments))
        self.assertEqual(1, sum(n.chain_coercion_type == 'float' for n in assignments))
        accesses = [n for n in expressions if isinstance(n, Index)]
        self.assertTrue(accesses)
        self.assertTrue(all(n.resolved_symbol.name == 'v' for n in accesses))
        symbol = accesses[0].resolved_symbol
        self.assertIs(symbol.dimension, symbol.declaration.size)
        self.assertEqual('2', expression_text(symbol.dimension))
        rows = []
        for n in expressions:
            symbol = n.resolved_symbol
            rows.append('\t'.join(map(str, (n.line, n.column, type(n).__name__,
                         n.semantic_type or '-', n.coercion_type or '-',
                         symbol.name if symbol else '-', symbol.scope if symbol else -1,
                         expression_text(symbol.dimension) if symbol and symbol.dimension else '-',
                         n.chain_coercion_type or '-'))))
        native = self.run_cli([self.annotations], source)
        self.assertEqual(0, native.returncode, native.stderr)
        self.assertEqual(sorted(rows), sorted(native.stdout.splitlines()))
        first = [(n.semantic_type, n.coercion_type) for n in expressions]
        analyzer.analyze(tree)
        self.assertEqual(first, [(n.semantic_type, n.coercion_type) for n in expressions])

    def test_error_annotations_suppress_cascades(self):
        source = 'int f() { int a[2]; return a[1.5]+true; }'
        tree, analyzer = self.annotated_tree(source)
        self.assertEqual(['SEM006'], [d.code for d in analyzer.diagnostics])
        binary = next(n for n in self.walk_nodes(tree) if isinstance(n, Binary))
        self.assertEqual(ERROR, binary.semantic_type)
        self.assertEqual(ERROR, binary.left.semantic_type)
        self.assertEqual('bool', binary.right.semantic_type)
        native = self.run_cli([self.annotations], source)
        self.assertEqual(0, native.returncode, native.stderr)
        error_rows = [line.split('\t')[2:4] for line in native.stdout.splitlines()
                      if line.split('\t')[3] == ERROR]
        self.assertEqual([['Binary', ERROR], ['Index', ERROR]], error_rows)

    def test_symbol_metadata(self):
        analyzer = analyze('int x; int f(int y) { { float x=1; } return y; }')
        self.assertEqual(['function','variable','parameter','variable'], [s.category for s in analyzer.symbols])
        xs = [s for s in analyzer.symbols if s.name == 'x']
        self.assertEqual(['int','float'], [s.type_name for s in xs])
        self.assertNotEqual(xs[0].scope, xs[1].scope)
        self.assertTrue(all(s.line >= 1 and s.column >= 1 for s in analyzer.symbols))

    def test_analyzer_reuse(self):
        analyzer = analyze('void f() { n=1; }')
        self.assertTrue(analyzer.diagnostics)
        self.assertFalse(analyze('void f() {}', analyzer).diagnostics)

    def test_lexical_syntax_and_io_exit_codes(self):
        for command in (['python3','minic.py'], [self.binary]):
            with self.subTest(command=command):
                self.assertEqual(2, self.run_cli(command, 'void f() { @; }').returncode)
                self.assertEqual(3, self.run_cli(command, 'void f( {}').returncode)
                result = subprocess.run(command+['/nonexistent/minic.c'],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(1,result.returncode)
                self.assertEqual('',result.stdout)
                self.assertTrue(result.stderr)


if __name__ == '__main__': unittest.main()
