"""
__main__.py (ir)
================
Ponto de entrada do pacote do Gerador de Representação Intermediária (IR / TAC).
Suporta interface gráfica via Tkinter e execução direta via CLI no terminal.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

try:
    from ..lexer.scanner import Scanner
    from ..parser.parser import Parser
    from ..ast.printer import print_tree
    from ..semantic.analyzer import SemanticAnalyzer, Diagnostic
    from .generator import generate_ir
    from .instructions import IRProgram
    from .printer import format_ir
    from ..optimizer.optimizer import optimize_ir
except (ImportError, ValueError):
    from ProjetoMiniC.src.lexer.scanner import Scanner
    from ProjetoMiniC.src.parser.parser import Parser
    from ProjetoMiniC.src.ast.printer import print_tree
    from ProjetoMiniC.src.semantic.analyzer import SemanticAnalyzer, Diagnostic
    from ProjetoMiniC.src.ir.generator import generate_ir
    from ProjetoMiniC.src.ir.instructions import IRProgram
    from ProjetoMiniC.src.ir.printer import format_ir
    from ProjetoMiniC.src.optimizer.optimizer import optimize_ir

EXTENSOES_SUPORTADAS = (
    ("Arquivos MiniC / C", "*.minic;*.mc;*.c;*.txt"),
    ("MiniC (*.minic)", "*.minic"),
    ("C (*.c)", "*.c"),
    ("Todos os arquivos", "*.*"),
)

CODIGO_EXEMPLO_IR = """int soma(int a, int b) {
    return a + b * 2;
}

float promove(int n) {
    return n;
}

int principal() {
    int i = 0;
    float x;
    i = soma(2, 3);
    x = promove(i) + 0.5;
    while (i < 10) {
        i = i + 1;
        if (i == 8) break;
    }
    print(x);
    return i;
}
"""


@dataclass
class ResultadoIR:
    ir_texto: str
    diagnosticos: list[str]
    arvore_ast: str
    tokens_texto: str
    codigo_saida: int
    ir_program: Optional[IRProgram] = None

    @property
    def sucesso(self) -> bool:
        return self.codigo_saida == 0


def analisar_ir(texto_fonte: str, optimize: bool = False) -> ResultadoIR:
    """Executa Lexer -> Parser -> Análise Semântica -> Geração de IR (e Otimização se optimize=True)."""
    scanner = Scanner(texto_fonte)
    scanner.scan_tokens()

    linhas_tokens = [
        f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}",
        "-" * 64,
    ]
    for token in scanner.tokens:
        nome, lexema, linha, coluna, atributo = token.para_linha_tabela()
        linhas_tokens.append(f"{nome:<14}{repr(lexema):<26}{linha:<7}{coluna:<8}{atributo}")
    tokens_str = "\n".join(linhas_tokens)

    if scanner.errors:
        diags = ["[ERRO LÉXICO] " + err.diagnostico() for err in scanner.errors]
        return ResultadoIR(
            ir_texto="",
            diagnosticos=diags,
            arvore_ast="",
            tokens_texto=tokens_str,
            codigo_saida=2,
        )

    parser = Parser(scanner.tokens, semantic_mode=True)
    programa = parser.parse()
    if programa is None or parser.errors:
        diags = [str(err) for err in parser.errors]
        return ResultadoIR(
            ir_texto="",
            diagnosticos=diags,
            arvore_ast="",
            tokens_texto=tokens_str,
            codigo_saida=3,
        )

    analyzer = SemanticAnalyzer()
    erros_sem: list[Diagnostic] = analyzer.analyze(programa)
    arvore_str = print_tree(programa)
    if erros_sem:
        diags = [str(err) for err in erros_sem]
        n = len(erros_sem)
        diags.append(
            f"Análise semântica concluída: {n} {'erro' if n == 1 else 'erros'}; programa rejeitado."
        )
        return ResultadoIR(
            ir_texto="",
            diagnosticos=diags,
            arvore_ast=arvore_str,
            tokens_texto=tokens_str,
            codigo_saida=4,
        )

    ir_prog = generate_ir(programa)
    if optimize:
        ir_prog = optimize_ir(ir_prog)
    ir_txt = format_ir(ir_prog)
    return ResultadoIR(
        ir_texto=ir_txt,
        diagnosticos=["Análise semântica concluída: 0 erros; programa aceito.", "IR gerado com sucesso."],
        arvore_ast=arvore_str,
        tokens_texto=tokens_str,
        codigo_saida=0,
        ir_program=ir_prog,
    )


class IRApp(tk.Tk):
    """Interface gráfica para o Gerador de Representação Intermediária (TAC)."""

    def __init__(self) -> None:
        super().__init__()
        self.title("MiniC - Gerador de IR (Código de Três Endereços)")
        self.geometry("1100x780")
        self.minsize(900, 600)
        self._resultado: Optional[ResultadoIR] = None
        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Gerador de Representação Intermediária (IR / TAC)",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Executa Lexer → Parser/AST → Análise Semântica → Geração de IR (Três Endereços).",
        ).pack(anchor="w", pady=(2, 12))

        barra = ttk.Frame(container)
        barra.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(barra, text="Gerar IR", command=self.analisar).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Abrir arquivo", command=self.abrir_arquivo).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Copiar IR", command=self.copiar_ir).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Limpar", command=self.limpar).pack(side=tk.LEFT)

        self.status = ttk.Label(barra, text="Pronto para gerar IR.", foreground="#40536d")
        self.status.pack(side=tk.RIGHT)

        ttk.Label(container, text="Código-fonte", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.campo_fonte = scrolledtext.ScrolledText(
            container, wrap=tk.NONE, height=14, undo=True, font=("Consolas", 10)
        )
        self.campo_fonte.insert("1.0", CODIGO_EXEMPLO_IR)
        self.campo_fonte.pack(fill=tk.BOTH, expand=True, pady=(4, 10))

        self.abas = ttk.Notebook(container)
        self.abas.pack(fill=tk.BOTH, expand=True)
        self.saida_ir = self._adicionar_aba("IR (Três Endereços)")
        self.saida_erros = self._adicionar_aba("Diagnósticos")
        self.saida_arvore = self._adicionar_aba("AST")
        self.saida_tokens = self._adicionar_aba("Tokens")

    def _adicionar_aba(self, titulo: str) -> scrolledtext.ScrolledText:
        frame = ttk.Frame(self.abas)
        self.abas.add(frame, text=titulo)
        texto = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state="disabled", font=("Consolas", 10))
        texto.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        return texto

    @staticmethod
    def _preencher(campo: scrolledtext.ScrolledText, conteudo: str) -> None:
        campo.configure(state="normal")
        campo.delete("1.0", tk.END)
        campo.insert("1.0", conteudo)
        campo.configure(state="disabled")

    def analisar(self) -> None:
        fonte = self.campo_fonte.get("1.0", tk.END).strip()
        if not fonte:
            messagebox.showwarning("Entrada vazia", "Digite algum código MiniC antes de gerar o IR.")
            return
        resultado = analisar_ir(fonte)
        self._resultado = resultado
        self._preencher(
            self.saida_ir,
            resultado.ir_texto if resultado.sucesso else "IR não gerado devido a erros nas etapas anteriores.",
        )
        self._preencher(self.saida_erros, "\n".join(resultado.diagnosticos))
        self._preencher(
            self.saida_arvore,
            resultado.arvore_ast or "AST não gerada devido aos erros.",
        )
        self._preencher(self.saida_tokens, resultado.tokens_texto)
        if resultado.sucesso:
            self.status.configure(text="ACEITO - IR gerado com sucesso.", foreground="#18733c")
            self.abas.select(0)
        else:
            mapa = {2: "léxico", 3: "sintático", 4: "semântico"}
            tipo = mapa.get(resultado.codigo_saida, "de compilação")
            self.status.configure(text=f"REJEITADO - erro {tipo}.", foreground="#a12622")
            self.abas.select(1)

    def abrir_arquivo(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo MiniC ou C", filetypes=EXTENSOES_SUPORTADAS
        )
        if not caminho:
            return
        try:
            fonte = Path(caminho).read_text(encoding="utf-8-sig")
        except OSError as erro:
            messagebox.showerror("Erro ao abrir arquivo", str(erro))
            return
        self.campo_fonte.delete("1.0", tk.END)
        self.campo_fonte.insert("1.0", fonte)
        self.title("MiniC - Gerador de IR - " + os.path.basename(caminho))
        self.analisar()

    def copiar_ir(self) -> None:
        if self._resultado is None or not self._resultado.ir_texto:
            messagebox.showwarning("IR indisponível", "Gere o IR de um programa válido antes de copiar.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._resultado.ir_texto)
        self.update_idletasks()
        messagebox.showinfo("Copiado", "IR copiado para a área de transferência.")

    def limpar(self) -> None:
        self.campo_fonte.delete("1.0", tk.END)
        self._resultado = None
        for campo in (self.saida_ir, self.saida_erros, self.saida_arvore, self.saida_tokens):
            self._preencher(campo, "")
        self.status.configure(text="Pronto para gerar IR.", foreground="#40536d")


def main(argv: Optional[list[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        optimize = False
        caminho_str: Optional[str] = None
        for arg in args:
            if arg == "-O1":
                optimize = True
            elif arg == "-O0":
                optimize = False
            elif arg == "--ir":
                continue
            elif caminho_str is None:
                caminho_str = arg
            else:
                print("Uso: python -m ProjetoMiniC.src.ir [-O0|-O1] <arquivo.c>", file=sys.stderr)
                return 1
        if caminho_str is None:
            print("Uso: python -m ProjetoMiniC.src.ir [-O0|-O1] <arquivo.c>", file=sys.stderr)
            return 1
        caminho = Path(caminho_str)
        if not caminho.exists() or not caminho.is_file():
            print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
            return 1
        try:
            conteudo = caminho.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            print(f"Erro ao ler arquivo: {exc}", file=sys.stderr)
            return 1
        res = analisar_ir(conteudo, optimize=optimize)
        if not res.sucesso:
            if res.codigo_saida in (2, 3):
                for line in res.diagnosticos:
                    print(line, file=sys.stderr)
            else:
                for line in res.diagnosticos:
                    print(line)
            return res.codigo_saida
        print(res.ir_texto)
        return 0

    try:
        app = IRApp()
        app.mainloop()
        return 0
    except tk.TclError as erro:
        print(f"Tkinter não pôde iniciar: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

