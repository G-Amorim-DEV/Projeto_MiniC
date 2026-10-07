#!/usr/bin/env bash
set -u

if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
    echo "Uso: bash testar_parser.sh <testes-parser-50> [parser.py] [parser.c]" >&2
    exit 2
fi

TEST_ROOT="$1"
PYTHON_PARSER="${2:-./parser.py}"
C_PARSER="${3:-./parser.c}"

status=0

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

if ! bash testar_parser_python.sh "$TEST_ROOT" "$PYTHON_PARSER" >"$tmp_dir/python.out"; then
    status=1
fi

if ! bash testar_parser_c.sh "$TEST_ROOT" "$C_PARSER" >"$tmp_dir/c.out"; then
    status=1
fi

cat "$tmp_dir/python.out"
if [ "$status" -ne 0 ]; then
    cat "$tmp_dir/c.out" >&2
fi
exit "$status"
