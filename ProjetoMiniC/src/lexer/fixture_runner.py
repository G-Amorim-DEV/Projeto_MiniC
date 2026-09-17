"""
fixture_runner.py
=================
Executa a validação em massa de fixtures de teste comparando os resultados
obtidos do Scanner com saídas .expected.jsonl e .errors.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Sequence

DIRETORIO_ATUAL = Path(__file__).resolve().parent.parent.parent.parent
if str(DIRETORIO_ATUAL) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_ATUAL))

from ProjetoMiniC.src.lexer.jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
from ProjetoMiniC.src.lexer.scanner import Scanner

SUFIXOS_ENTRADA: Sequence[str] = (".minic", ".mc", ".c", "")


def _remover_sufixo(texto: str, sufixo: str) -> str:
    """Remove sufixos de extensoes para localizar arquivos associados."""
    if texto.endswith(sufixo):
        return texto[:-len(sufixo)]
    return texto


def _ler_jsonl(caminho: Path) -> List[dict]:
    """Lê um arquivo JSONL e converte cada linha em um dicionário Python."""
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines() if linha.strip()]


def _obter_entradas_candidatas(arquivo_esperado: Path) -> List[Path]:
    """Mapeia os arquivos de entrada correspondentes a um arquivo de resposta esperada."""
    base = _remover_sufixo(arquivo_esperado.name, ".expected.jsonl")
    candidatos: List[Path] = []
    for sufixo in SUFIXOS_ENTRADA:
        candidato = arquivo_esperado.with_name(base + sufixo)
        if candidato.exists():
            candidatos.append(candidato)
    return candidatos


def executar_fixture(arquivo_esperado: Path, arquivo_entrada: Path, raiz: Path) -> bool:
    """Executa a análise no arquivo de entrada e compara com os resultados esperados em arquivo."""
    fonte = arquivo_entrada.read_text(encoding="utf-8")
    scanner = Scanner(fonte)
    scanner.scan_tokens()

    texto_tokens_obtido = serialize_tokens_jsonl(scanner.tokens)
    registros_obtidos = [json.loads(linha) for linha in texto_tokens_obtido.splitlines() if linha.strip()]
    registros_esperados = _ler_jsonl(arquivo_esperado)

    if registros_obtidos != registros_esperados:
        print(f"FALHA: {arquivo_esperado.relative_to(raiz)} (Tokens gerados não coincidem com os esperados)")
        return False

    arquivo_erros = arquivo_esperado.with_name(arquivo_esperado.name.replace(".expected.jsonl", ".errors.jsonl"))
    if arquivo_erros.exists():
        texto_erros_obtido = serialize_errors_jsonl(scanner.erros)
        registros_erros_obtidos = [json.loads(linha) for linha in texto_erros_obtido.splitlines() if linha.strip()]
        registros_erros_esperados = _ler_jsonl(arquivo_erros)

        if registros_erros_obtidos != registros_erros_esperados:
            print(f"FALHA: {arquivo_erros.relative_to(raiz)} (Lista de erros difere da esperada)")
            return False

    print(f"SUCESSO: {arquivo_esperado.relative_to(raiz)}")
    return True


def descobrir_fixtures(raiz: Path) -> List[tuple[Path, Path]]:
    """Localiza todos os pares de arquivos de teste (.expected.jsonl e fontes) na pasta raiz."""
    fixtures: List[tuple[Path, Path]] = []
    for arquivo_esperado in sorted(raiz.rglob("*.expected.jsonl")):
        candidatos = _obter_entradas_candidatas(arquivo_esperado)
        if candidatos:
            fixtures.append((arquivo_esperado, candidatos[0]))
    return fixtures


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa testes automatizados baseados em fixtures no scanner MiniC.")
    parser.add_argument("raiz", nargs="?", default=".", help="Diretório raiz para busca de fixtures")
    args = parser.parse_args()

    raiz = Path(args.raiz).resolve()
    fixtures = descobrir_fixtures(raiz)

    if not fixtures:
        print("Nenhum arquivo de fixture encontrado.")
        return 1

    aprovados = 0
    falhas = 0
    for esperado, entrada in fixtures:
        if executar_fixture(esperado, entrada, raiz):
            aprovados += 1
        else:
            falhas += 1

    print(f"\nResumo da Suíte de Testes: APROVADOS={aprovados} | FALHAS={falhas}")
    return 0 if falhas == 0 else 2


if __name__ == "__main__":
    sys.exit(main())