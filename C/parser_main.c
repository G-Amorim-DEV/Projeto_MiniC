#include "parser.h"
#include "scanner.h"
#include "util.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "Uso: ./parser <arquivo.c | arquivo.minic>\n"); return 1; }
    char *source = read_file(argv[1]); if (!source) { fprintf(stderr, "Erro: Arquivo '%s' não encontrado.\n", argv[1]); return 1; }
    Scanner scanner; scanner_init(&scanner, source); scanner_scan_tokens(&scanner);
    if (scanner_has_errors(&scanner)) { scanner_print_errors(&scanner); scanner_free(&scanner); free(source); return 2; }
    Parser parser; parser_init(&parser, scanner.tokens, scanner.tokens_len); AstNode *root = parser_parse(&parser);
    if (!root) { scanner_free(&scanner); free(source); return 3; }
    char *text = ast_to_sexpr(root); puts(text); free(text); ast_free(root); scanner_free(&scanner); free(source); return 0;
}
