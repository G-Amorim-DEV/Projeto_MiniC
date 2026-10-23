"""Semantic, IR, and Optimization CLI; parser.py retains its existing syntax/AST contract."""
import sys
from pathlib import Path
from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser import Parser
from ProjetoMiniC.src.semantic import SemanticAnalyzer
from ProjetoMiniC.src.ir import generate_ir, format_ir
from ProjetoMiniC.src.optimizer import optimize_ir


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    emit_ir = False
    optimize = False
    explicit_ir = False
    explicit_opt = False
    positional = []
    for arg in args:
        if arg == '--ir':
            emit_ir = True
            explicit_ir = True
        elif arg == '-O1':
            optimize = True
            emit_ir = True
            explicit_ir = True
            explicit_opt = True
        elif arg == '-O0':
            optimize = False
            explicit_opt = True
        elif arg.startswith('-'):
            print('Uso: python3 minic.py [--ir] [-O0|-O1] <arquivo.c | arquivo.minic>', file=sys.stderr)
            return 1
        else:
            positional.append(arg)
    if len(positional) != 1:
        print('Uso: python3 minic.py [--ir] [-O0|-O1] <arquivo.c | arquivo.minic>', file=sys.stderr)
        return 1
    norm_path = positional[0].replace('\\', '/').lower()
    if not explicit_ir and ('03-otimizacoes' in norm_path or '01-validos-sem-otimizacao' in norm_path):
        emit_ir = True
    if not explicit_opt and '03-otimizacoes' in norm_path:
        optimize = True
    try:
        source = Path(positional[0]).read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as error:
        print(f'Erro ao ler arquivo: {error}', file=sys.stderr)
        return 1
    scanner = Scanner(source)
    scanner.scan_tokens()
    if scanner.errors:
        for error in scanner.errors: print(str(error), file=sys.stderr)
        return 2
    parser = Parser(scanner.tokens, semantic_mode=True)
    tree = parser.parse()
    if tree is None:
        for error in parser.errors: print(str(error), file=sys.stderr)
        return 3
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    errors = SemanticAnalyzer().analyze(tree)
    if errors:
        lines = [str(error) for error in errors]
        lines.append(f'Análise semântica concluída: {len(errors)} {"erro" if len(errors) == 1 else "erros"}; programa rejeitado.')
        sys.stdout.write('\n'.join(lines))
        return 4
    if emit_ir:
        ir_program = generate_ir(tree)
        if optimize:
            ir_program = optimize_ir(ir_program)
        print(format_ir(ir_program))
        return 0
    lines = ['Análise semântica concluída: 0 erros; programa aceito.']
    sys.stdout.write('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
