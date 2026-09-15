"""Entrada CLI da Etapa 2: ``python parser.py arquivo.c``."""

import sys
from pathlib import Path

from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser import Parser


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Uso: python parser.py <arquivo.c | arquivo.minic>", file=sys.stderr)
        return 1
    path = Path(args[0])
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print("Erro ao ler arquivo '{}': {}".format(path, error), file=sys.stderr)
        return 1
    scanner = Scanner(source)
    scanner.scan_tokens()
    if scanner.errors:
        for error in scanner.errors: print("Erro léxico: " + error.diagnostic(), file=sys.stderr)
        return 2
    parser = Parser(scanner.tokens)
    tree = parser.parse()
    if parser.errors:
        for error in parser.errors: print(str(error), file=sys.stderr)
        return 3
    print(tree.to_sexpr())
    return 0


if __name__ == "__main__":
    sys.exit(main())
