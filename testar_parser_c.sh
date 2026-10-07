#!/usr/bin/env bash
set -u

if [ "$#" -ne 2 ]; then
    echo "Uso: bash testar_parser_c.sh <testes-parser-50> <parser.c>" >&2
    exit 2
fi

TEST_ROOT="$1"
PARSER_ARG="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER_PATH="$(cd "$(dirname "$PARSER_ARG")" && pwd)/$(basename "$PARSER_ARG")"

if [ -d "$TEST_ROOT/casos" ]; then
    CASES_DIR="$(cd "$TEST_ROOT/casos" && pwd)"
elif [ -d "$TEST_ROOT/testes-parser-50/casos" ]; then
    CASES_DIR="$(cd "$TEST_ROOT/testes-parser-50/casos" && pwd)"
else
    echo "ERRO: pasta casos não encontrada em $TEST_ROOT" >&2
    exit 2
fi

if [ ! -f "$PARSER_PATH" ]; then
    echo "ERRO: parser não encontrado: $PARSER_PATH" >&2
    exit 2
fi

if ! command -v gcc >/dev/null 2>&1; then
    echo "ERRO: GCC não encontrado. Instale GCC/MinGW para executar o parser C." >&2
    exit 2
fi

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
elif command -v py >/dev/null 2>&1; then
    PYTHON_CMD=(py -3)
else
    PYTHON_CMD=()
    for candidate in /c/Users/*/AppData/Local/Programs/Python/Python*/python.exe; do
        if [ -f "$candidate" ]; then
            PYTHON_CMD=("$candidate")
            break
        fi
    done
fi

if [ "${#PYTHON_CMD[@]}" -eq 0 ]; then
    echo "ERRO: Python não encontrado para comparar as ASTs." >&2
    exit 2
fi

same_ast() {
    "${PYTHON_CMD[@]}" - "$1" "$2" <<'PY'
import sys

def normalize(text):
    result = []
    quoted = False
    escaped = False
    for char in text:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\" and quoted:
            result.append(char)
            escaped = True
        elif char in ("'", '"'):
            result.append(char)
            quoted = not quoted
        elif char.isspace() and not quoted:
            continue
        else:
            result.append(char)
    return "".join(result)

actual = normalize(open(sys.argv[1], encoding="utf-8", errors="replace").read())
expected = normalize(open(sys.argv[2], encoding="utf-8-sig", errors="replace").read())
sys.exit(0 if actual == expected else 1)
PY
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
BINARY="$TMP_DIR/parser"

gcc -std=c11 -Wall -Wextra -pedantic -O2 "$PARSER_PATH" -o "$BINARY" || exit 2
if [ ! -x "$BINARY" ] && [ -x "$BINARY.exe" ]; then
    BINARY="$BINARY.exe"
fi

NATIVE_PATH="$BINARY"
if command -v cygpath >/dev/null 2>&1; then
    NATIVE_PATH="$(cygpath -w "$BINARY")"
fi
exec "${PYTHON_CMD[@]}" "$SCRIPT_DIR/test_parser_50.py" "$CASES_DIR" --native "$NATIVE_PATH"

passed=0
failed=0
count=0

for case_dir in "$CASES_DIR"/*; do
    [ -d "$case_dir" ] || continue
    source="$case_dir/codigo.c"
    expected="$case_dir/ast.esperada.txt"
    [ -f "$source" ] || continue
    count=$((count + 1))
    id="$(basename "$case_dir" | cut -d_ -f1)"
    actual="$TMP_DIR/$id.out"
    error="$TMP_DIR/$id.err"
    "$BINARY" "$source" >"$actual" 2>"$error"
    status=$?

    if [ "$id" -le 25 ]; then
        if [ "$status" -eq 0 ] && same_ast "$actual" "$expected"; then
            echo "$id | ACEITO"
            passed=$((passed + 1))
        else
            echo "$id | FALHOU"
            cat "$error" >&2
            failed=$((failed + 1))
        fi
    elif [ "$status" -ne 0 ]; then
        echo "$id | REJEITADO"
        passed=$((passed + 1))
    else
        echo "$id | FALHOU (entrada inválida aceita)"
        failed=$((failed + 1))
    fi
done

echo "Resumo: $passed/$count casos passaram."
[ "$count" -eq 50 ] && [ "$failed" -eq 0 ]
