"""Semantic and IR CLI; parser.py retains its existing syntax/AST contract."""
import sys
from pathlib import Path
from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser import Parser
from ProjetoMiniC.src.semantic import SemanticAnalyzer
from ProjetoMiniC.src.ir import generate_ir, format_ir


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    emit_ir = False
    if '--ir' in args:
        emit_ir = True
        args = [a for a in args if a != '--ir']
    if len(args) != 1 or args[0].startswith('-'):
        print('Uso: python3 minic.py [--ir] <arquivo.c | arquivo.minic>', file=sys.stderr)
        return 1
    try:
        source = Path(args[0]).read_text(encoding='utf-8-sig')
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
    errors = SemanticAnalyzer().analyze(tree)
    if errors:
        lines = [str(error) for error in errors]
        lines.append(f'Análise semântica concluída: {len(errors)} {"erro" if len(errors) == 1 else "erros"}; programa rejeitado.')
        sys.stdout.buffer.write('\r\n'.join(lines).encode('utf-8'))
        return 4
    if emit_ir:
        ir_program = generate_ir(tree)
        print(format_ir(ir_program))
        return 0
    lines = ['Análise semântica concluída: 0 erros; programa aceito.']
    sys.stdout.buffer.write('\r\n'.join(lines).encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
