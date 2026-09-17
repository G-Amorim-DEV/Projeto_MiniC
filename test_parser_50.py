"""Valida os 50 casos oficiais do analisador sintático MiniC."""

import argparse
import difflib
import subprocess
import sys
from pathlib import Path

from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser.parser import Parser

DIAGNOSTICOS = {
    26: ("PONTO_E_VIRGULA",), 27: ("PONTO_E_VIRGULA",), 28: ("FECHA_PAREN",),
    29: ("ABRE_CHAVE",), 30: ("FECHA_CHAVE",), 31: ("IDENT", "FECHA_PAREN"),
    32: ("KW_",), 33: ("IDENT",), 34: ("KW_", "FECHA_PAREN"),
    35: ("expressão",), 36: ("expressão",), 37: ("expressão",),
    38: ("expressão",), 39: ("FECHA_PAREN",), 40: ("FECHA_PAREN", "expressão"),
    41: ("FECHA_COLCHETE",), 42: ("expressão",), 43: ("início de statement",),
    44: ("KW_ELSE inesperado",), 45: ("PONTO_E_VIRGULA",), 46: ("IDENT",),
    47: ("IDENT",), 48: ("ABRE_CHAVE",), 49: ("FECHA_CHAVE inesperado",),
    50: ("expressão",),
}


def localizar_casos(root, informado):
    candidatos = [informado] if informado else []
    candidatos += [root / "testes-parser-50" / "testes-parser-50" / "casos"]
    return next((p.resolve() for p in candidatos if p and p.is_dir()), None)


def executar(parser_path, case_dir):
    return subprocess.run(
        [sys.executable, str(parser_path), str(case_dir / "codigo.c")],
        cwd=parser_path.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def dados_execucao(case_dir):
    fonte = (case_dir / "codigo.c").read_text(encoding="utf-8")
    scanner = Scanner(fonte)
    scanner.scan_tokens()
    parser = Parser(scanner.tokens)
    arvore = parser.parse() if not scanner.errors else None
    tokens = ["{} {!r} linha {} coluna {}".format(t.type.name, t.lexeme, t.line, t.column) for t in scanner.tokens]
    return scanner, parser, arvore, tokens


def main():
    root = Path(__file__).resolve().parent
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cases_dir", nargs="?", type=Path)
    cli.add_argument("--detalhado", action="store_true")
    args = cli.parse_args()
    cases_dir = localizar_casos(root, args.cases_dir)
    if cases_dir is None:
        print("ERRO: pasta oficial dos casos não encontrada.", file=sys.stderr)
        return 2
    cases = sorted(p for p in cases_dir.iterdir() if p.is_dir() and (p / "codigo.c").is_file())
    if len(cases) != 50:
        print("ERRO: esperados 50 casos; encontrados {}.".format(len(cases)), file=sys.stderr)
        return 2

    counts = {"validos": 0, "invalidos": 0, "ast": 0, "diag": 0, "scanner": 0}
    falhas = []
    for case in cases:
        numero = int(case.name.split("_", 1)[0])
        resultado = executar(root / "parser.py", case)
        esperado_ast = (case / "ast.esperada.txt").read_text(encoding="utf-8").strip()
        esperado_diag = (case / "resultado.esperado.txt").read_text(encoding="utf-8").strip()
        scanner, parser, arvore, tokens = dados_execucao(case)
        counts["scanner"] += not scanner.errors
        ast_ok = numero > 25 or (resultado.returncode == 0 and resultado.stdout.strip() == esperado_ast)
        diag_ok = numero <= 25 or (resultado.returncode != 0 and any(item.casefold() in resultado.stderr.casefold() for item in DIAGNOSTICOS[numero]))
        status_ok = (resultado.returncode == 0) if numero <= 25 else (resultado.returncode != 0 and not resultado.stdout.strip())
        if numero <= 25:
            counts["validos"] += status_ok
            counts["ast"] += ast_ok
        else:
            counts["invalidos"] += status_ok
            counts["diag"] += diag_ok
        ok = status_ok and ast_ok and diag_ok and not scanner.errors
        if not ok:
            falhas.append(case.name)
        print("[{}] {}".format("OK" if ok else "FALHOU", case.name))

        if args.detalhado:
            obtida = resultado.stdout.strip() or "Não gerada devido aos erros."
            diagnostico = resultado.stderr.strip() or "Nenhum erro sintático encontrado."
            diff = "\n".join(difflib.unified_diff(esperado_ast.splitlines(), obtida.splitlines(), lineterm=""))
            print("=" * 60)
            print("CASO {:02d}/50 — {}\n\nENTRADA:\n{}".format(numero, case.name, (case / "codigo.c").read_text().strip()))
            print("\nRESULTADO ESPERADO:\n{}".format("ACEITO" if numero <= 25 else "REJEITADO"))
            print("\nAST ESPERADA:\n{}\n\nAST OBTIDA:\n{}".format(esperado_ast or "Não deve existir.", obtida))
            print("\nDIAGNÓSTICO ESPERADO:\n{}\n\nDIAGNÓSTICO OBTIDO:\n{}".format(esperado_diag, diagnostico))
            print("\nTOKENS:\n{}\n\nÁRVORE DESCENDENTE:\n{}".format("\n".join(tokens), parser.trace_text()))
            print("\nVALIDAÇÃO:\nScanner: {}\nParser: {}\nAST: {}\nDiagnóstico: {}\nResultado esperado: {}".format(
                "OK" if not scanner.errors else "FALHOU", "OK" if status_ok else "FALHOU",
                "OK" if ast_ok else "FALHOU", "OK" if diag_ok else "FALHOU", "OK" if ok else "FALHOU"))
            if diff and numero <= 25:
                print("\nDIFF DA AST:\n" + diff)
            print("=" * 60)

    total = 50 - len(falhas)
    print("\nResumo:\nVálidos: {}/25\nInválidos: {}/25\nAST exata: {}/25\nDiagnósticos: {}/25\nScanner: {}/50\nTOTAL: {}/50".format(
        counts["validos"], counts["invalidos"], counts["ast"], counts["diag"], counts["scanner"], total))
    if not falhas:
        print("\n50/50 APROVADOS")
    else:
        print("\nFalhas: " + ", ".join(falhas))
    return 0 if not falhas else 1


if __name__ == "__main__":
    raise SystemExit(main())
