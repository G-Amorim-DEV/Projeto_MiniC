"""Executa os 50 casos externos de regressao do parser MiniC."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def read_expected(path):
    return path.read_text(encoding="utf-8-sig").strip()


def read_manifest(cases_dir):
    manifest_path = cases_dir.parent / "manifesto.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["casos"]}


def normalize_ast(text):
    """Remove apenas espaços de formatação, preservando valores entre aspas."""
    normalized = []
    quoted = False
    escaped = False
    for character in text:
        if escaped:
            normalized.append(character)
            escaped = False
        elif character == "\\" and quoted:
            normalized.append(character)
            escaped = True
        elif character in ("'", '"'):
            normalized.append(character)
            quoted = not quoted
        elif character.isspace() and not quoted:
            continue
        else:
            normalized.append(character)
    return "".join(normalized)


def run_case(parser_path, case_dir, native_path=None):
    source_path = case_dir / "codigo.c"
    expected_path = case_dir / "ast.esperada.txt"
    command = (
        [str(native_path), str(source_path)]
        if native_path is not None
        else [sys.executable, str(parser_path), str(source_path)]
    )
    result = subprocess.run(
        command,
        cwd=parser_path.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    number = int(case_dir.name.split("_", 1)[0])
    expected = read_expected(expected_path)

    if number <= 25:
        actual = result.stdout.strip()
        passed = result.returncode == 0 and normalize_ast(actual) == normalize_ast(expected)
        if result.returncode != 0:
            detail = result.stderr.strip()
        elif not passed:
            detail = "AST diferente\n  gerada: " + actual + "\n  esperada: " + expected
        else:
            detail = "AST equivalente"
    else:
        passed = result.returncode != 0
        detail = "aceitou entrada invalida" if result.returncode == 0 else "rejeitou"

    return passed, detail


def main():
    project_root = Path(__file__).resolve().parent
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "cases_dir",
        nargs="?",
        type=Path,
        default=None,
        help="pasta casos do pacote testes-parser-50",
    )
    argument_parser.add_argument(
        "--native",
        type=Path,
        default=None,
        help="executável nativo do parser C",
    )
    args = argument_parser.parse_args()
    candidates = []
    if args.cases_dir is not None:
        candidates.append(args.cases_dir)
    candidates.extend(
        [
            Path.home() / "Downloads" / "testes-parser-50" / "testes-parser-50" / "casos",
            project_root.parent / "testes-parser-50" / "testes-parser-50" / "casos",
        ]
    )
    cases_dir = next(
        (candidate.resolve() for candidate in candidates if candidate.is_dir()),
        None,
    )

    if cases_dir is None:
        print(
            "ERRO: pasta dos casos não encontrada. Informe o caminho, por exemplo:\n"
            '  python test_parser_50.py "C:\\caminho\\testes-parser-50\\testes-parser-50\\casos"',
            file=sys.stderr,
        )
        return 2

    case_dirs = sorted(
        path for path in cases_dir.iterdir()
        if path.is_dir() and (path / "codigo.c").is_file()
    )

    if len(case_dirs) != 50:
        print(
            "ERRO: esperados 50 casos com codigo.c; encontrados {} em {}".format(
                len(case_dirs), cases_dir
            ),
            file=sys.stderr,
        )
        return 2

    manifest = read_manifest(cases_dir)
    parser_path = project_root / "parser.py"
    passed = 0
    failed = []
    results = []
    for case_dir in case_dirs:
        ok, detail = run_case(parser_path, case_dir, args.native)
        case_id = int(case_dir.name.split("_", 1)[0])
        if ok:
            passed += 1
            status = "ACEITO" if case_id <= 25 else "REJEITADO"
        else:
            failed.append((case_dir.name, detail))
            status = "FALHOU"
        item = manifest.get(case_id, {})
        results.append((case_id, status, item.get("titulo", case_dir.name), item.get("diretorio", "")))

    print("ID | STATUS | TÍTULO | DIRETÓRIO")
    for case_id, status, title, directory in results:
        print("{:02d} | {} | {} | {}".format(case_id, status, title, directory))
    print("\nResumo: {}/{} casos passaram.".format(passed, len(case_dirs)))
    for name, detail in failed:
        print("- {}: {}".format(name, detail))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())