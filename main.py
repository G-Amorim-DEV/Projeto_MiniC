"""
main.py
=======

Ponto de entrada do compilador MiniC.
Compatível com Python 3.8+ em qualquer SO (Linux, macOS, Windows).

Modos de Execução:
1. Terminal / Automação / Correção Automática:
   python main.py arquivo.minic
   python main.py arquivo.minic --tokens
   python main.py arquivo.minic --errors
   python main.py arquivo.minic --jsonl
   python main.py arquivo.minic --parse     (roda o parser e informa OK/erros sintáticos)
   python main.py arquivo.minic --ast       (roda o parser e imprime a AST em árvore)
   python main.py arquivo.minic --ast --sexp (imprime a AST em forma parentetizada)

2. Interface Gráfica (Tkinter):
   python main.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# ======================================================================
# RESOLUÇÃO UNIVERSAL DE PATHS
# ======================================================================
DIRETORIO_ARQUIVO = Path(__file__).resolve().parent

# Adiciona o diretório do main.py e subpastas possíveis ao sys.path
candidatos_path = [
    DIRETORIO_ARQUIVO,
    DIRETORIO_ARQUIVO / "ProjetoMiniC" / "Python",
    DIRETORIO_ARQUIVO.parent,
]

for p in candidatos_path:
    if p.exists() and (p / "src").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
        DIRETORIO_BASE = p
        break
else:
    DIRETORIO_BASE = DIRETORIO_ARQUIVO
    if str(DIRETORIO_BASE) not in sys.path:
        sys.path.insert(0, str(DIRETORIO_BASE))

try:
    from ProjetoMiniC.src.lexer.jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
    from ProjetoMiniC.src.lexer.scanner import Scanner
    from ProjetoMiniC.src.parser.parser import Parser
    from ProjetoMiniC.src.ast.printer import print_tree, to_sexp
except ModuleNotFoundError as exc:
    print(f"Erro de importação no compilador: {exc}", file=sys.stderr)
    sys.exit(1)


# ======================================================================
# MODO TERMINAL (CLI / CORRETOR AUTOMÁTICO)
# ======================================================================

def executar_terminal(argumentos: list[str]) -> int:
    caminho_alvo: str | None = None
    mostrar_tokens = False
    mostrar_erros = False
    modo_jsonl = False
    mostrar_ast = False
    apenas_parse = False
    formato_sexp = False

    for arg in argumentos:
        if arg == "--tokens":
            mostrar_tokens = True
        elif arg == "--errors":
            mostrar_erros = True
        elif arg == "--jsonl":
            modo_jsonl = True
        elif arg == "--ast":
            mostrar_ast = True
        elif arg == "--parse":
            apenas_parse = True
        elif arg == "--sexp":
            formato_sexp = True
        elif not arg.startswith("--") and caminho_alvo is None:
            caminho_alvo = arg

    if not caminho_alvo:
        print("Uso: python main.py <arquivo.minic> [--tokens] [--errors] [--jsonl] [--parse] [--ast] [--sexp]",
              file=sys.stderr)
        return 1

    arquivo = Path(caminho_alvo)
    if not arquivo.exists() or not arquivo.is_file():
        print(f"Erro: Arquivo '{caminho_alvo}' não encontrado.", file=sys.stderr)
        return 1

    try:
        conteudo = arquivo.read_text(encoding="utf-8")
    except OSError as err:
        print(f"Erro ao ler arquivo: {err}", file=sys.stderr)
        return 1

    scanner = Scanner(conteudo)
    scanner.scan_tokens()

    # ------------------------------------------------------------------
    # Etapa 2: Parser + AST (não substitui os modos do lexer já existentes)
    # ------------------------------------------------------------------
    if mostrar_ast or apenas_parse:
        parser = Parser(scanner.tokens)
        programa = parser.parse()

        if scanner.possui_erros():
            print(f"{len(scanner.erros)} erro(s) léxico(s) encontrado(s):", file=sys.stderr)
            for err in scanner.erros:
                print(f"  [ERRO LÉXICO] {err.diagnostico()}", file=sys.stderr)

        if parser.possui_erros():
            print(f"{len(parser.erros)} erro(s) sintático(s) encontrado(s):", file=sys.stderr)
            for err in parser.erros:
                print(f"  [ERRO SINTÁTICO] {err.diagnostico()}", file=sys.stderr)
        elif apenas_parse and not mostrar_ast:
            print("Análise sintática concluída sem erros.")

        if mostrar_ast:
            if formato_sexp:
                print(to_sexp(programa))
            else:
                print(print_tree(programa))

        if scanner.possui_erros():
            return 2
        return 3 if parser.possui_erros() else 0

    # Formato JSONL (padrão dos fixtures do professor)
    if modo_jsonl:
        if not mostrar_erros:
            saida_tokens = serialize_tokens_jsonl(scanner.tokens)
            if saida_tokens:
                print(saida_tokens)
        if not mostrar_tokens and scanner.erros:
            saida_erros = serialize_errors_jsonl(scanner.erros)
            if saida_erros:
                print(saida_erros, file=sys.stderr)

    elif mostrar_tokens:
        cabecalho = f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}"
        print(cabecalho)
        print("-" * len(cabecalho))
        for tok in scanner.tokens:
            nome, lexema, linha, coluna, attr = tok.para_linha_tabela()
            print(f"{nome:<14}{repr(lexema):<26}{linha:<7}{coluna:<8}{attr}")

    elif mostrar_erros:
        if scanner.erros:
            print(f"{len(scanner.erros)} erro(s) léxico(s) encontrado(s):", file=sys.stderr)
            for err in scanner.erros:
                print(f"  [ERRO LÉXICO] {err.diagnostico()}", file=sys.stderr)
        else:
            print("Nenhum erro léxico encontrado.")

    else:
        print("=" * 80)
        print(f"Análise Léxica - Arquivo: {arquivo.name}")
        print("=" * 80)
        print("Tokens reconhecidos:")
        scanner.imprimir_tokens()
        print("-" * 80)
        print("Diagnóstico:")
        scanner.imprimir_erros()

    return 2 if scanner.possui_erros() else 0


# ======================================================================
# MODO INTERFACE GRÁFICA (LAUNCHER)
# ======================================================================

def _launch_module(module_name: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(DIRETORIO_BASE) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        subprocess.Popen(
            [sys.executable, "-m", module_name],
            cwd=str(DIRETORIO_BASE),
            env=env,
        )
    except OSError as exc:
        print(f"Não foi possível iniciar {module_name}: {exc}", file=sys.stderr)


def iniciar_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        print("Tkinter indisponível neste ambiente.", file=sys.stderr)
        print("Uso: python main.py <arquivo.minic>", file=sys.stderr)
        return 1

    class LauncherApp(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.title("Compilador MiniC - Painel")
            self.geometry("1000x560")
            self.configure(bg="#1f1f23")
            self._construir_interface()

        def _construir_interface(self) -> None:
            header = tk.Label(self, text="Compilador de C em Python", fg="white", bg="#1f1f23", font=("Segoe UI", 20, "bold"))
            header.pack(pady=(24, 8))

            subtitle = tk.Label(self, text="Grupo 1 - 6 CCAM", fg="#cfcfff", bg="#1f1f23", font=("Segoe UI", 12))
            subtitle.pack(pady=(0, 18))

            frame = tk.Frame(self, bg="#1f1f23")
            frame.pack(expand=True)

            botoes = [
                ("Análise Léxica", lambda: _launch_module("ProjetoMiniC.src.lexer")),
                ("Gerador de IR", lambda: messagebox.showinfo("Em desenvolvimento", "Gerador de IR ainda não implementado.")),
                ("Análise Sintática", lambda: _launch_module("ProjetoMiniC.src.parser")),
                ("Análise Semântica", lambda: messagebox.showinfo("Em desenvolvimento", "Análise semântica ainda não implementada.")),
                ("Gerador de Código", lambda: messagebox.showinfo("Em desenvolvimento", "Gerador de código ainda não implementado.")),
                ("Otimizador", lambda: messagebox.showinfo("Em desenvolvimento", "Otimizador ainda não implementado.")),
            ]

            for idx, (label, cmd) in enumerate(botoes):
                r = idx // 3
                c = idx % 3
                btn = tk.Button(
                    frame,
                    text=label,
                    command=cmd,
                    bg="#4b6ef6",
                    fg="white",
                    activebackground="#6f8bff",
                    activeforeground="white",
                    font=("Segoe UI", 12, "bold"),
                    bd=0,
                    padx=24,
                    pady=14,
                )
                btn.grid(row=r, column=c, padx=40, pady=18, ipadx=10, ipady=6, sticky="nsew")

            for i in range(3):
                frame.grid_columnconfigure(i, weight=1)

    try:
        app = LauncherApp()
        app.mainloop()
        return 0
    except tk.TclError:
        print("Ambiente sem display gráfico (headless).", file=sys.stderr)
        print("Uso: python main.py <arquivo.minic> [--tokens] [--errors] [--jsonl]", file=sys.stderr)
        return 1


def main() -> int:
    if len(sys.argv) > 1:
        return executar_terminal(sys.argv[1:])
    return iniciar_gui()


if __name__ == "__main__":
    sys.exit(main())
