"""
__main__.py
===========
Ponto de entrada do pacote do Lexer. Suporta interface gráfica via Tkinter
e execução direta via CLI no terminal.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .analysis_result import ResultadoAnalise, VisaoAnalise
from .demo import CODIGO_TESTE_1, CODIGO_TESTE_2, CODIGO_TESTE_3
from .jsonl_serializer import serialize_errors_jsonl, serialize_tokens_jsonl
from .scanner import Scanner

EXTENSOES_SUPORTADAS = (
    ("Arquivos MiniC / C", "*.minic;*.mc;*.c;*.txt"),
    ("MiniC (*.minic)", "*.minic"),
    ("C (*.c)", "*.c"),
    ("Todos os arquivos", "*.*"),
)


def formatar_saida_scanner(scanner: Scanner, texto_fonte: str, titulo: str = "Análise Léxica") -> str:
    """Gera um relatório de saída completo formatado em string."""
    linhas: list[str] = []
    linhas.append("=" * 80)
    linhas.append(titulo)
    linhas.append("=" * 80)
    linhas.append("Código-fonte:")
    linhas.append(texto_fonte)
    linhas.append("-" * 80)
    linhas.append("Tokens reconhecidos:")

    if not scanner.tokens:
        linhas.append("Nenhum token foi gerado.")
    else:
        cabecalho = f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}"
        linhas.append(cabecalho)
        linhas.append("-" * len(cabecalho))
        for token in scanner.tokens:
            nome, lexema, linha, coluna, atributo = token.para_linha_tabela()
            lexema_repr = repr(lexema)
            if len(lexema_repr) > 24:
                lexema_repr = lexema_repr[:21] + "...'"
            linhas.append(f"{nome:<14}{lexema_repr:<26}{linha:<7}{coluna:<8}{atributo}")

    linhas.append("-" * 80)
    linhas.append("Diagnóstico:")
    if scanner.erros:
        linhas.append(f"{len(scanner.erros)} erro(s) léxico encontrado(s):")
        for erro in scanner.erros:
            linhas.append(f"  [ERRO LÉXICO] {erro.diagnostico()}")
    else:
        linhas.append("Nenhum erro léxico encontrado.")

    linhas.append("-" * 80)
    linhas.append("Saída em Formato JSONL (Tokens):")
    tokens_jsonl = serialize_tokens_jsonl(scanner.tokens)
    linhas.append(tokens_jsonl if tokens_jsonl else "(vazio)")

    if scanner.erros:
        linhas.append("-" * 80)
        linhas.append("Saída em Formato JSONL (Erros):")
        erros_jsonl = serialize_errors_jsonl(scanner.erros)
        linhas.append(erros_jsonl if erros_jsonl else "(vazio)")

    return "\n".join(linhas)


def escanear_texto(texto: str, titulo: str = "Análise Léxica") -> str:
    """Instancia o scanner para o texto informado e retorna o relatório impresso."""
    scanner = Scanner(texto)
    scanner.scan_tokens()
    return formatar_saida_scanner(scanner, texto, titulo)


def executar_testes_embutidos() -> str:
    """Executa a bateria de código contida em `demo.py`."""
    fonte = "\n\n".join((CODIGO_TESTE_1, CODIGO_TESTE_2, CODIGO_TESTE_3))
    return escanear_texto(fonte, "Testes Embutidos (demo.py)")


def construir_visao_analise(texto_fonte: str, titulo: str, caminho: Path | None = None) -> VisaoAnalise:
    """Compila os dados da execução do Scanner na classe `VisaoAnalise` para consumo pela GUI."""
    scanner = Scanner(texto_fonte)
    scanner.scan_tokens()
    resultado = ResultadoAnalise(tokens=scanner.tokens, erros=scanner.erros)
    return VisaoAnalise(
        titulo=titulo,
        fonte=texto_fonte,
        resultado=resultado,
        saida_formatada=formatar_saida_scanner(scanner, texto_fonte, titulo),
        tokens_jsonl=serialize_tokens_jsonl(scanner.tokens),
        erros_jsonl=serialize_errors_jsonl(scanner.erros) if scanner.erros else "",
        caminho_fonte=caminho,
    )


def executar_modo_terminal(argumentos: list[str]) -> int:
    """Execução CLI do módulo quando acionado no terminal."""
    caminho_arquivo: str | None = None
    mostrar_apenas_tokens = False
    mostrar_apenas_erros = False
    modo_jsonl = False

    for arg in argumentos:
        if arg == "--tokens":
            mostrar_apenas_tokens = True
        elif arg == "--errors":
            mostrar_apenas_erros = True
        elif arg == "--jsonl":
            modo_jsonl = True
        elif not arg.startswith("--") and caminho_arquivo is None:
            caminho_arquivo = arg

    if not caminho_arquivo:
        print("Uso: python -m src.lexer <arquivo.minic> [--tokens] [--errors] [--jsonl]", file=sys.stderr)
        return 1

    caminho = Path(caminho_arquivo)
    if not caminho.exists() or not caminho.is_file():
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.", file=sys.stderr)
        return 1

    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Erro ao ler arquivo '{caminho_arquivo}': {exc}", file=sys.stderr)
        return 1

    scanner = Scanner(conteudo)
    scanner.scan_tokens()

    if modo_jsonl:
        if not mostrar_apenas_erros:
            saida_tokens = serialize_tokens_jsonl(scanner.tokens)
            if saida_tokens:
                print(saida_tokens)
        if not mostrar_apenas_tokens and scanner.erros:
            saida_erros = serialize_errors_jsonl(scanner.erros)
            if saida_erros:
                print(saida_erros, file=sys.stderr)
    elif mostrar_apenas_tokens:
        cabecalho = f"{'TIPO':<14}{'LEXEMA':<26}{'LINHA':<7}{'COLUNA':<8}{'ATRIBUTO'}"
        print(cabecalho)
        print("-" * len(cabecalho))
        for token in scanner.tokens:
            nome, lexema, linha, coluna, atributo = token.para_linha_tabela()
            print(f"{nome:<14}{repr(lexema):<26}{linha:<7}{coluna:<8}{atributo}")
    elif mostrar_apenas_erros:
        if scanner.erros:
            for erro in scanner.erros:
                print(f"[ERRO LÉXICO] {erro.diagnostico()}", file=sys.stderr)
        else:
            print("Nenhum erro léxico encontrado.")
    else:
        print(formatar_saida_scanner(scanner, conteudo, f"Arquivo: {caminho.name}"))

    return 2 if scanner.possui_erros() else 0


class AplicacaoLexer(tk.Tk):
    """Interface gráfica interativa desenvolvida em Tkinter."""
    def __init__(self) -> None:
        super().__init__()
        self.title("MiniC - Analisador Léxico")
        self.geometry("1100x780")
        self.minsize(950, 600)
        self.configure(bg="#f2f4f7")
        self._visao_atual: VisaoAnalise | None = None
        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        titulo = ttk.Label(container, text="Analisador Léxico MiniC", font=("Segoe UI", 16, "bold"))
        titulo.pack(anchor="w", pady=(0, 10))

        barra_botoes = ttk.Frame(container)
        barra_botoes.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(barra_botoes, text="Executar testes embutidos", command=self.executar_testes).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra_botoes, text="Analisar código digitado", command=self.executar_texto_digitado).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra_botoes, text="Abrir arquivo MiniC / C", command=self.abrir_arquivo).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra_botoes, text="Copiar JSONL", command=self.copiar_jsonl).pack(side=tk.LEFT)

        self.campo_texto = scrolledtext.ScrolledText(
            container,
            wrap=tk.WORD,
            height=12,
            font=("Consolas", 10),
            padx=8,
            pady=8,
        )
        self.campo_texto.insert(
            tk.END,
            "int main() {\n"
            "    int x = 10;\n"
            "    if (x > 0 && x != 0) {\n"
            "        print(x);\n"
            "    }\n"
            "    return 0;\n"
            "}\n",
        )
        self.campo_texto.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.abas = ttk.Notebook(container)
        self.abas.pack(fill=tk.BOTH, expand=True)

        aba_formatada = ttk.Frame(self.abas)
        aba_json = ttk.Frame(self.abas)
        aba_erros = ttk.Frame(self.abas)

        self.abas.add(aba_formatada, text="Saída Formatada")
        self.abas.add(aba_json, text="Tokens JSONL (.expected.jsonl)")
        self.abas.add(aba_erros, text="Erros JSONL (.errors.jsonl)")

        self.txt_formatado = scrolledtext.ScrolledText(aba_formatada, wrap=tk.WORD, state="disabled", font=("Consolas", 10))
        self.txt_formatado.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.txt_json = scrolledtext.ScrolledText(aba_json, wrap=tk.WORD, state="disabled", font=("Consolas", 10))
        self.txt_json.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.txt_erros = scrolledtext.ScrolledText(aba_erros, wrap=tk.WORD, state="disabled", font=("Consolas", 10))
        self.txt_erros.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _renderizar_visao(self, visao: VisaoAnalise) -> None:
        """Renderiza a estrutura da visão nos componentes de texto da interface."""
        self._visao_atual = visao

        self.txt_formatado.configure(state="normal")
        self.txt_formatado.delete("1.0", tk.END)
        self.txt_formatado.insert(tk.END, visao.saida_formatada)
        self.txt_formatado.configure(state="disabled")

        self.txt_json.configure(state="normal")
        self.txt_json.delete("1.0", tk.END)
        self.txt_json.insert(tk.END, visao.tokens_jsonl)
        self.txt_json.configure(state="disabled")

        self.txt_erros.configure(state="normal")
        self.txt_erros.delete("1.0", tk.END)
        self.txt_erros.insert(tk.END, visao.erros_jsonl or "Nenhum erro léxico encontrado.")
        self.txt_erros.configure(state="disabled")

    def executar_testes(self) -> None:
        fonte = "\n\n".join((CODIGO_TESTE_1, CODIGO_TESTE_2, CODIGO_TESTE_3))
        visao = construir_visao_analise(fonte, "Testes Embutidos (demo.py)")
        self._renderizar_visao(visao)

    def executar_texto_digitado(self) -> None:
        fonte = self.campo_texto.get("1.0", tk.END).strip()
        if not fonte:
            messagebox.showwarning("Entrada vazia", "Digite algum código MiniC antes de analisar.")
            return
        visao = construir_visao_analise(fonte, "Texto Digitado")
        self._renderizar_visao(visao)

    def abrir_arquivo(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo MiniC ou C",
            filetypes=EXTENSOES_SUPORTADAS,
        )
        if not caminho:
            return

        try:
            with open(caminho, "r", encoding="utf-8") as arq:
                fonte = arq.read()
        except OSError as exc:
            messagebox.showerror("Erro ao abrir arquivo", str(exc))
            return

        self.campo_texto.delete("1.0", tk.END)
        self.campo_texto.insert(tk.END, fonte)
        visao = construir_visao_analise(fonte, f"Arquivo: {os.path.basename(caminho)}", Path(caminho))
        self._renderizar_visao(visao)

    def copiar_jsonl(self) -> None:
        if not self._visao_atual:
            messagebox.showwarning("Aviso", "Execute uma análise antes de copiar o JSONL.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._visao_atual.tokens_jsonl)
        self.update_idletasks()
        messagebox.showinfo("Copiado", "Tokens JSONL copiados para a área de transferência.")


def main() -> int:
    if len(sys.argv) > 1:
        return executar_modo_terminal(sys.argv[1:])

    try:
        app = AplicacaoLexer()
        app.mainloop()
        return 0
    except tk.TclError:
        print("Interface Tkinter indisponível. Executando modo texto demonstrativo.")
        print(executar_testes_embutidos())
        return 0


if __name__ == "__main__":
    sys.exit(main())