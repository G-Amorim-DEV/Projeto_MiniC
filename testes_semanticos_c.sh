#!/usr/bin/env bash
set -uo pipefail

if (($# != 2)); then
  echo "Uso: $0 [arquivo_fonte] [diretorio]" >&2
  exit 2
fi

arquivo_fonte=$1
diretorio=$2

if [[ ! -f "$arquivo_fonte" ]]; then
  echo "Erro: arquivo-fonte não encontrado: $arquivo_fonte" >&2
  exit 2
fi

if [[ ! -d "$diretorio" ]]; then
  echo "Erro: diretório de testes não encontrado: $diretorio" >&2
  exit 2
fi

if ! command -v gcc >/dev/null 2>&1; then
  echo "Erro: gcc não está disponível." >&2
  exit 2
fi

tmp_dir=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp_dir"' EXIT
executavel="$tmp_dir/analisador"

echo "Compilando o analisador com gcc..."
if ! gcc -Wall -Wextra "$arquivo_fonte" -o "$executavel"; then
  echo "Erro: a compilação do analisador falhou." >&2
  exit 2
fi

total=0
aprovados=0
reprovados=0

while IFS= read -r -d '' teste; do
  total=$((total + 1))
  gabarito="${teste%.c}.gabarito"
  saida="$tmp_dir/saida-$total.txt"

  if [[ ! -f "$gabarito" ]]; then
    printf '[FALHA] %s — gabarito não encontrado\n' "$teste"
    reprovados=$((reprovados + 1))
    continue
  fi

  "$executavel" "$teste" >"$saida" 2>&1 || true

  tr -d '\r' < "$gabarito" > "$tmp_dir/norm_gabarito-$total.txt"
  tr -d '\r' < "$saida" > "$tmp_dir/norm_saida-$total.txt"

  if diff -u "$tmp_dir/norm_gabarito-$total.txt" "$tmp_dir/norm_saida-$total.txt" >"$tmp_dir/diff-$total.txt"; then
    printf '[OK]     %s\n' "$teste"
    aprovados=$((aprovados + 1))
  else
    printf '[FALHA] %s\n' "$teste"
    cat "$tmp_dir/diff-$total.txt"
    reprovados=$((reprovados + 1))
  fi
done < <(find "$diretorio" -type f -name '*.c' -print0 | sort -z)

if ((total == 0)); then
  echo "Erro: nenhum arquivo .c encontrado em $diretorio" >&2
  exit 2
fi

printf '\nResultado: %d/%d aprovados; %d reprovados.\n' \
  "$aprovados" "$total" "$reprovados"

# ======================================================================
# DETALHAMENTO DAS SAÍDAS E DIAGNÓSTICOS (AULA 15)
# ======================================================================
echo ""
echo "______________________________________________________________________"
echo "DETALHAMENTO DAS SAÍDAS E DIAGNÓSTICOS GERADOS (GABARITO AULA 15):"
echo "______________________________________________________________________"

cont_aceitos=0
cont_rejeitados=0
num=0

while IFS= read -r -d '' teste; do
  num=$((num + 1))
  saida="$tmp_dir/saida-$num.txt"
  nome_teste=$(basename "$teste")

  echo ""
  echo "[$num] Teste: $nome_teste"
  if grep -q "programa aceito" "$saida"; then
    echo "Status Semântico: ACEITO"
    cont_aceitos=$((cont_aceitos + 1))
  else
    echo "Status Semântico: REJEITADO (Erros semânticos detectados)"
    cont_rejeitados=$((cont_rejeitados + 1))
  fi

  echo "Saída / Diagnóstico:"
  sed 's/^/  /' "$saida"
  echo ""
  echo "______________________________________________________________________"
done < <(find "$diretorio" -type f -name '*.c' -print0 | sort -z)

echo ""
printf 'Resumo Semântico: %d aceitos | %d rejeitados (Total: %d casos)\n' \
  "$cont_aceitos" "$cont_rejeitados" "$num"

if ((reprovados == 0)); then
  exit 0
else
  exit 1
fi
