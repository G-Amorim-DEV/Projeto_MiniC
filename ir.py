"""Entrada CLI da Etapa de Representação Intermediária (IR): ``python ir.py arquivo.c``."""

import sys
from minic import main as minic_main


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--ir" not in args:
        args.insert(0, "--ir")
    return minic_main(args)


if __name__ == "__main__":
    sys.exit(main())

