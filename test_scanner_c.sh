#!/usr/bin/env bash
# Testa um analisador léxico escrito em C com arquivos .c e .minic.
#
# Uso:
#   ./test_scanner_c.sh [scanner.c] [pasta-de-testes]
#
# O scanner deve aceitar:
#   ./scanner arquivo.c --jsonl
#   ./scanner arquivo.minic --jsonl
#
# A saída padrão deve conter um objeto JSON por linha, compatível com os
# arquivos <entrada>.expected.jsonl. Diagnósticos esperados podem ser
# armazenados em <entrada>.errors.jsonl.

set -euo pipefail

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCANNER_SOURCE="${1:-scanner.c}"
TESTS_DIR="${2:-.}"
SCANNER_BINARY="./scanner"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TOTAL=0
PASS=0
FAIL=0
WARN=0

compare_jsonl() {
    local actual="$1" expected="$2" kind="${3:-tokens}"
    "$PYTHON_BIN" - "$actual" "$expected" "$kind" <<'PY'
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

actual_path, expected_path, kind = sys.argv[1:4]

def read_jsonl(path):
    values = []
    p = Path(path)
    if not p.exists():
        return values
    for number, line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if not line.strip():
            continue
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f'FALHA: JSON inválido em {path}:{number}: {exc}')
            sys.exit(1)
    return values

def first_difference(got, want):
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else '<ausente>'
        b = want[i] if i < len(want) else '<a mais>'
        if a != b:
            print(f'  primeira diferença na posição {i + 1}:')
            print(f'    esperado: {json.dumps(b, ensure_ascii=False)}')
            print(f'    obtido:   {json.dumps(a, ensure_ascii=False)}')
            return

produced = read_jsonl(actual_path)
expected = read_jsonl(expected_path)
if kind == 'tokens':
    produced_items = [x for x in produced if 'token' in x]
else:
    produced_items = [x for x in produced if 'error' in x]

if produced_items != expected:
    print(f'FALHA: sequência de {kind} diferente.')
    first_difference(produced_items, expected)
    sys.exit(1)

print(f'OK: {len(produced_items)} {kind}.')
sys.exit(0)
PY
}

run_case() {
    local input="$1" expected="$2" label="${1#./}"
    local errors_expected="${expected%.expected.jsonl}.errors.jsonl"
    TOTAL=$((TOTAL + 1))
    printf '\n================================================================\nCaso: %s\n' "$label"
    printf 'Comando: %s %s --jsonl\n' "$SCANNER_BINARY" "$input"
    printf 'Resultado esperado: %s\n' "$expected"

    local expected_status=0
    if [[ -f "$errors_expected" ]]; then
        expected_status=2
    fi

    set +e
    "$SCANNER_BINARY" "$input" --jsonl > output_tokens.jsonl 2> output_errors.jsonl
    status=$?
    set -e

    local case_failed=0

    if ! compare_jsonl output_tokens.jsonl "$expected" "tokens"; then
        echo 'RESULTADO: FALHOU — tokens diferentes do esperado'
        case_failed=1
    fi

    if [[ -f "$errors_expected" ]]; then
        if ! compare_jsonl output_errors.jsonl "$errors_expected" "erros"; then
            echo 'RESULTADO: FALHOU — erros diferentes do esperado'
            case_failed=1
        fi
    else
        if [[ -s output_errors.jsonl ]]; then
            echo 'RESULTADO: FALHOU — erros inesperados emitidos'
            case_failed=1
        fi
    fi

    if (( status != expected_status )); then
        echo "RESULTADO: FALHOU — código de saída $status (esperado: $expected_status)"
        case_failed=1
    fi

    if (( case_failed == 0 )); then
        echo 'RESULTADO: OK'
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
    fi
}

printf '%s\n' '== Compilando o analisador léxico =='
gcc -Wall -Wextra -std=c11 "$SCANNER_SOURCE" -o "$SCANNER_BINARY"
printf 'Executável gerado: %s\n' "$SCANNER_BINARY"

mapfile -t expected_files < <(find "$TESTS_DIR" -type f -name '*.expected.jsonl' -print | sort)
(( ${#expected_files[@]} > 0 )) || { echo "ERRO: nenhum resultado esperado para .c ou .minic foi encontrado." >&2; exit 2; }

for expected in "${expected_files[@]}"; do
    input="${expected%.expected.jsonl}"
    if [[ -f "$input" || -f "$input.minic" || -f "$input.c" ]]; then
        if [[ -f "$input" ]]; then
            run_case "$input" "$expected"
        elif [[ -f "$input.minic" ]]; then
            run_case "$input.minic" "$expected"
        elif [[ -f "$input.c" ]]; then
            run_case "$input.c" "$expected"
        fi
    else
        echo "AVISO: entrada correspondente não encontrada para $expected" >&2
        WARN=$((WARN + 1))
    fi
done

rm -f output_tokens.jsonl output_errors.jsonl

printf '\n================================================================\n'
printf 'Resumo: %d OK, %d falharam, %d avisos, %d casos verificados.\n' "$PASS" "$FAIL" "$WARN" "$TOTAL"
(( FAIL == 0 && WARN == 0 ))
