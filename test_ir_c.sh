#!/usr/bin/env bash
set -u

uso() {
  printf 'Uso: %s [arquivo_fonte.c] [diretorio_dos_testes]\n' "$0" >&2
  printf 'Exemplo: %s ./minic.c ./minic-ir-test-cases\n' "$0" >&2
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/test_ir_30.py" ]]; then
  REPO_ROOT="$SCRIPT_DIR"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if [[ $# -eq 0 ]]; then
  FONTE="$REPO_ROOT/minic.c"
  SUITE="$REPO_ROOT/minic-ir-test-cases"
elif [[ $# -eq 2 ]]; then
  if [[ -d "$1" && -f "$2" ]]; then
    SUITE="${1%/}"
    FONTE="$2"
  else
    FONTE="$1"
    SUITE="${2%/}"
  fi
else
  uso
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'Erro: Python não encontrado.\n' >&2
    exit 2
  fi
fi

[[ -f "$FONTE" ]] || { printf 'Erro: fonte C não encontrada: %s\n' "$FONTE" >&2; exit 2; }
[[ -d "$SUITE" ]] || { printf 'Erro: diretório de testes não encontrado: %s\n' "$SUITE" >&2; exit 2; }

RUNNER="$REPO_ROOT/test_ir_30.py"
if command -v cygpath >/dev/null 2>&1; then
  RUNNER="$(cygpath -w "$RUNNER")"
  FONTE="$(cygpath -w "$FONTE")"
  SUITE="$(cygpath -w "$SUITE")"
fi

exec "$PYTHON_BIN" "$RUNNER" --c "$FONTE" "$SUITE"

