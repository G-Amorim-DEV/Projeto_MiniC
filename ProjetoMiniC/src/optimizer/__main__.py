"""
__main__.py (optimizer)
=======================
Ponto de entrada do pacote do Otimizador de Representação Intermediária (-O1).
Suporta interface gráfica via Tkinter e execução direta via CLI no terminal.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

try:
    from ..ir.__main__ import EXTENSOES_SUPORTADAS, ResultadoIR, analisar_ir
except (ImportError, ValueError):
    from ProjetoMiniC.src.ir.__main__ import EXTENSOES_SUPORTADAS, ResultadoIR, analisar_ir

CODIGO_EXEMPLO_OPT = """int main() {
    int a = 2 + 3;
    int b = a * 4;
    print(b);
    return 0;
}
"""


class OptimizerApp(tk.Tk):
    """Interface gráfica para o Otimizador de IR (-O0 vs -O1)."""

    def __init__(self) -> None:
        super().__init__()
        self.title("MiniC - Otimizador de IR (-O1)")
        self.geometry("1120x780")
        self.minsize(900, 600)
        self._res_o0: Optional[ResultadoIR] = None
        self._res_o1: Optional[ResultadoIR] = None
        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Otimizador de Representação Intermediária (-O1)",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Compara a IR sem otimização (-O0) com a IR otimizada (-O1).",
        ).pack(anchor="w", pady=(2, 12))

        barra = ttk.Frame(container)
        barra.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(barra, text="Otimizar IR (-O1)", command=self.analisar).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(barra, text="Abrir arquivo", command=self.abrir_arquivo).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(barra, text="Copiar IR (-O1)", command=self.copiar_ir).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(barra, text="Limpar", command=self.limpar).pack(side=tk.LEFT)

        self.status = ttk.Label(
            barra, text="Pronto para otimizar IR.", foreground="#40536d"
        )
        self.status.pack(side=tk.RIGHT)

        ttk.Label(container, text="Código-fonte", font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        self.campo_fonte = scrolledtext.ScrolledText(
            container, wrap=tk.NONE, height=13, undo=True, font=("Consolas", 10)
        )
        self.campo_fonte.insert("1.0", CODIGO_EXEMPLO_OPT)
        self.campo_fonte.pack(fill=tk.BOTH, expand=True, pady=(4, 10))

        self.abas = ttk.Notebook(container)
        self.abas.pack(fill=tk.BOTH, expand=True)
        self.saida_o1 = self._adicionar_aba("IR Otimizada (-O1)")
        self.saida_o0 = self._adicionar_aba("IR Sem Otimização (-O0)")
        self.saida_erros = self._adicionar_aba("Diagnósticos")

    def _adicionar_aba(self, titulo: str) -> scrolledtext.ScrolledText:
        frame = ttk.Frame(self.abas)
        self.abas.add(frame, text=titulo)
        texto = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, state="disabled", font=("Consolas", 10)
        )
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
            messagebox.showwarning(
                "Entrada vazia", "Digite algum código MiniC antes de otimizar."
            )
            return
        res_o0 = analisar_ir(fonte, optimize=False)
        res_o1 = analisar_ir(fonte, optimize=True)
        self._res_o0 = res_o0
        self._res_o1 = res_o1
        self._preencher(
            self.saida_o1,
            res_o1.ir_texto
            if res_o1.sucesso
            else "IR não gerada devido a erros nas etapas anteriores.",
        )
        self._preencher(
            self.saida_o0,
            res_o0.ir_texto
            if res_o0.sucesso
            else "IR não gerada devido a erros nas etapas anteriores.",
        )
        self._preencher(self.saida_erros, "\n".join(res_o1.diagnosticos))
        if res_o1.sucesso:
            self.status.configure(
                text="ACEITO - IR otimizada (-O1) com sucesso.", foreground="#18733c"
            )
            self.abas.select(0)
        else:
            mapa = {2: "léxico", 3: "sintático", 4: "semântico"}
            tipo = mapa.get(res_o1.codigo_saida, "de compilação")
            self.status.configure(
                text=f"REJEITADO - erro {tipo}.", foreground="#a12622"
            )
            self.abas.select(2)

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
        self.title("MiniC - Otimizador de IR - " + os.path.basename(caminho))
        self.analisar()

    def copiar_ir(self) -> None:
        if self._res_o1 is None or not self._res_o1.ir_texto:
            messagebox.showwarning(
                "IR indisponível", "Otimize um programa válido antes de copiar."
            )
            return
        self.clipboard_clear()
        self.clipboard_append(self._res_o1.ir_texto)
        self.update_idletasks()
        messagebox.showinfo("Copiado", "IR (-O1) copiada para a área de transferência.")

    def limpar(self) -> None:
        self.campo_fonte.delete("1.0", tk.END)
        self._res_o0 = None
        self._res_o1 = None
        for campo in (self.saida_o1, self.saida_o0, self.saida_erros):
            self._preencher(campo, "")
        self.status.configure(text="Pronto para otimizar IR.", foreground="#40536d")


def main(argv: Optional[list[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        caminho_str = None
        for a in args:
            if a not in ("-O0", "-O1", "--ir"):
                caminho_str = a
        if not caminho_str:
            print("Uso: python -m ProjetoMiniC.src.optimizer [-O0|-O1] <arquivo.c>", file=sys.stderr)
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
        opt = "-O0" not in args
        res = analisar_ir(conteudo, optimize=opt)
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
        app = OptimizerApp()
        app.mainloop()
        return 0
    except tk.TclError as erro:
        print(f"Tkinter não pôde iniciar: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

