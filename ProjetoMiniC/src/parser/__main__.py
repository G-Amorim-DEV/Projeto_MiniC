"""Interface gráfica para o analisador sintático MiniC."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ProjetoMiniC.src.lexer.scanner import Scanner
from ProjetoMiniC.src.parser.parser import Parser


EXTENSOES_SUPORTADAS = (
    ("Arquivos MiniC / C", "*.minic;*.mc;*.c;*.txt"),
    ("MiniC (*.minic)", "*.minic"),
    ("C (*.c)", "*.c"),
    ("Todos os arquivos", "*.*"),
)

EXEMPLO = """int soma(int a, int b) {
    return a + b;
}

int main() {
    int resultado = soma(2, 3);
    print(resultado);
    return 0;
}
"""


@dataclass
class ResultadoSintatico:
    ast: str
    diagnosticos: list[str]
    tokens: list[str]
    codigo_saida: int

    @property
    def sucesso(self) -> bool:
        return self.codigo_saida == 0


def analisar_fonte(fonte: str) -> ResultadoSintatico:
    """Executa scanner e parser, retornando dados próprios para a interface."""
    scanner = Scanner(fonte)
    scanner.scan_tokens()
    tokens = [
        "{:<14} {:<20} linha {:<4} coluna {}".format(
            token.type.name, repr(token.lexeme), token.line, token.column
        )
        for token in scanner.tokens
    ]
    if scanner.errors:
        return ResultadoSintatico(
            ast="",
            diagnosticos=["[ERRO LÉXICO] " + erro.diagnostic() for erro in scanner.errors],
            tokens=tokens,
            codigo_saida=2,
        )

    parser = Parser(scanner.tokens)
    arvore = parser.parse()
    if parser.errors:
        return ResultadoSintatico(
            ast="",
            diagnosticos=[str(erro) for erro in parser.errors],
            tokens=tokens,
            codigo_saida=3,
        )

    return ResultadoSintatico(
        ast=arvore.to_sexpr() if arvore is not None else "",
        diagnosticos=[],
        tokens=tokens,
        codigo_saida=0,
    )


class ParserApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MiniC - Analisador Sintático")
        self.geometry("1100x780")
        self.minsize(900, 600)
        self._resultado: ResultadoSintatico | None = None
        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Analisador Sintático MiniC",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Digite ou abra um programa para gerar sua árvore sintática abstrata (AST).",
        ).pack(anchor="w", pady=(2, 12))

        barra = ttk.Frame(container)
        barra.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(barra, text="Analisar código", command=self.analisar).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Abrir arquivo", command=self.abrir_arquivo).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Copiar AST", command=self.copiar_ast).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Limpar", command=self.limpar).pack(side=tk.LEFT)

        self.status = ttk.Label(barra, text="Pronto para analisar.", foreground="#40536d")
        self.status.pack(side=tk.RIGHT)

        ttk.Label(container, text="Código-fonte", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.campo_fonte = scrolledtext.ScrolledText(
            container, wrap=tk.NONE, height=16, undo=True, font=("Consolas", 10)
        )
        self.campo_fonte.insert("1.0", EXEMPLO)
        self.campo_fonte.pack(fill=tk.BOTH, expand=True, pady=(4, 10))

        self.abas = ttk.Notebook(container)
        self.abas.pack(fill=tk.BOTH, expand=True)
        self.saida_ast = self._adicionar_aba("AST")
        self.saida_erros = self._adicionar_aba("Diagnósticos")
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
            messagebox.showwarning("Entrada vazia", "Digite algum código MiniC antes de analisar.")
            return
        resultado = analisar_fonte(fonte)
        self._resultado = resultado
        self._preencher(self.saida_ast, resultado.ast or "AST não gerada devido aos erros.")
        self._preencher(
            self.saida_erros,
            "\n".join(resultado.diagnosticos) or "Nenhum erro léxico ou sintático encontrado.",
        )
        self._preencher(self.saida_tokens, "\n".join(resultado.tokens))
        if resultado.sucesso:
            self.status.configure(text="Análise concluída com sucesso.", foreground="#18733c")
            self.abas.select(0)
        else:
            tipo = "léxico" if resultado.codigo_saida == 2 else "sintático"
            self.status.configure(text="Análise concluída com erro {}.".format(tipo), foreground="#a12622")
            self.abas.select(1)

    def abrir_arquivo(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo MiniC ou C", filetypes=EXTENSOES_SUPORTADAS
        )
        if not caminho:
            return
        try:
            fonte = Path(caminho).read_text(encoding="utf-8")
        except OSError as erro:
            messagebox.showerror("Erro ao abrir arquivo", str(erro))
            return
        self.campo_fonte.delete("1.0", tk.END)
        self.campo_fonte.insert("1.0", fonte)
        self.title("MiniC - Analisador Sintático - " + os.path.basename(caminho))
        self.analisar()

    def copiar_ast(self) -> None:
        if self._resultado is None or not self._resultado.ast:
            messagebox.showwarning("AST indisponível", "Execute uma análise válida antes de copiar a AST.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._resultado.ast)
        self.update_idletasks()
        messagebox.showinfo("Copiado", "AST copiada para a área de transferência.")

    def limpar(self) -> None:
        self.campo_fonte.delete("1.0", tk.END)
        self._resultado = None
        for campo in (self.saida_ast, self.saida_erros, self.saida_tokens):
            self._preencher(campo, "")
        self.status.configure(text="Pronto para analisar.", foreground="#40536d")


def main() -> int:
    try:
        app = ParserApp()
        app.mainloop()
        return 0
    except tk.TclError as erro:
        print("Tkinter não pôde iniciar: {}".format(erro), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
