"""
demo.py
=======
Módulo para testes locais rápidos do analisador léxico da linguagem MiniC.
"""

from .scanner import Scanner

CODIGO_TESTE_1 = """int main() {
    int total = 2 + 3 * 4;
    // mostra o resultado calculado
    print(total);
    return 0;
}"""

CODIGO_TESTE_2 = """int main() {
    int x = 10 @ 5;
    char msg = "texto sem fechamento;
    return 0;
}"""

CODIGO_TESTE_3 = """int main() {
    int a = 1;
    int b = 2;
    if (a < b && b != 0 || !a) {
        print(a);
    }
    /* comentario de bloco sem fechamento
    return 0;
}"""


def executar_caso_teste(titulo: str, codigo_fonte: str) -> Scanner:
    """Executa o scanner para um trecho de código e exibe relatórios no terminal."""
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)
    print("Código-fonte:")
    print(codigo_fonte)
    print("-" * 78)

    scanner = Scanner(codigo_fonte)
    scanner.scan_tokens()

    print("Tokens reconhecidos:")
    scanner.imprimir_tokens()

    print("-" * 78)
    print("Diagnóstico:")
    scanner.imprimir_erros()

    return scanner


def main() -> None:
    s1 = executar_caso_teste("Caso 1 - Código válido sem erros", CODIGO_TESTE_1)
    s2 = executar_caso_teste("Caso 2 - Símbolo inválido (@) e string não fechada", CODIGO_TESTE_2)
    s3 = executar_caso_teste("Caso 3 - Operadores lógicos e comentário de bloco aberto", CODIGO_TESTE_3)

    print("\n" + "=" * 78)
    print("Resumo dos Testes de Demonstração")
    print("=" * 78)
    for i, scanner in enumerate((s1, s2, s3), start=1):
        total_tokens = max(0, len(scanner.tokens) - 1)
        status = "COM ERROS" if scanner.possui_erros() else "OK"
        print(f"Teste {i}: {total_tokens} token(s) | {len(scanner.erros)} erro(s) léxico(s) | Status={status}")


if __name__ == "__main__":
    main()