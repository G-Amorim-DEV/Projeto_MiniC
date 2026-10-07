"""
scanner.py
==========
Ponto de entrada raiz com resolução automática para subpastas.
"""

import sys
from pathlib import Path 

# Adiciona a subpasta ProjetoMiniC ao sys.path
DIRETORIO_RAIZ = Path(__file__).resolve().parent
for caminho in (DIRETORIO_RAIZ, DIRETORIO_RAIZ / "ProjetoMiniC"):
    if caminho.exists() and str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

# Resolve o argumento do arquivo caso o caminho tenha sido passado relativo à subpasta
if len(sys.argv) > 1:
    for i, arg in enumerate(sys.argv[1:], start=1):
        if not arg.startswith("--"):
            caminho_informado = Path(arg)
            if not caminho_informado.exists():
                caminho_alternativo = DIRETORIO_RAIZ / "ProjetoMiniC" / arg
                if caminho_alternativo.exists():
                    sys.argv[i] = str(caminho_alternativo)
            break

from ProjetoMiniC.src.lexer.scanner import Scanner, main

if __name__ == "__main__":
    sys.exit(main())
