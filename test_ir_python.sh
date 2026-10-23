#!/usr/bin/env bash
set -u

uso() {
  echo "Uso: $0 [caminho/minic.py] [diretorio_dos_testes]" >&2
  echo "Exemplo: $0 ./minic.py ./minic-ir-test-cases" >&2
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/test_ir_30.py" ]]; then
  REPO_ROOT="$SCRIPT_DIR"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if [[ $# -eq 0 ]]; then
  MINIC_PY="$REPO_ROOT/minic.py"
  SUITE="$REPO_ROOT/minic-ir-test-cases"
elif [[ $# -eq 2 ]]; then
  if [[ -d "$1" && -f "$2" ]]; then
    SUITE="${1%/}"
    MINIC_PY="$2"
  else
    MINIC_PY="$1"
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
    echo "Erro: Python não encontrado." >&2
    exit 2
  fi
fi

[[ -f "$MINIC_PY" ]] || {
  echo "Erro: não encontrei o compilador: $MINIC_PY" >&2
  exit 2
}
[[ -d "$SUITE" ]] || {
  echo "Erro: não encontrei o diretório de testes: $SUITE" >&2
  exit 2
}

RUNNER="$REPO_ROOT/test_ir_30.py"
if command -v cygpath >/dev/null 2>&1; then
  RUNNER="$(cygpath -w "$RUNNER")"
  MINIC_PY="$(cygpath -w "$MINIC_PY")"
  SUITE="$(cygpath -w "$SUITE")"
fi

exec "$PYTHON_BIN" "$RUNNER" --python "$MINIC_PY" "$SUITE"

