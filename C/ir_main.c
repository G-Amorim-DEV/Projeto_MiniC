#include "ir.h"
#include "parser.h"
#include "scanner.h"
#include "semantic.h"
#include "util.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *filepath = NULL;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--ir") == 0) {
            continue;
        } else if (argv[i][0] == '-' || filepath) {
            fprintf(stderr, "Uso: ./ir <arquivo.c | arquivo.minic>\n");
            return 1;
        } else {
            filepath = argv[i];
        }
    }
    if (!filepath) {
        fprintf(stderr, "Uso: ./ir <arquivo.c | arquivo.minic>\n");
        return 1;
    }
    char *source = read_file(filepath);
    if (!source) {
        fprintf(stderr, "Erro ao ler arquivo '%s'.\n", filepath);
        return 1;
    }
    Scanner scanner;
    scanner_init(&scanner, source);
    scanner_scan_tokens(&scanner);
    if (scanner_has_errors(&scanner)) {
        scanner_print_errors(&scanner);
        scanner_free(&scanner);
        free(source);
        return 2;
    }
    Parser parser;
    parser_init(&parser, scanner.tokens, scanner.tokens_len);
    parser.semantic_mode = 1;
    AstNode *root = parser_parse(&parser);
    if (!root) {
        scanner_free(&scanner);
        free(source);
        return 3;
    }
    int errors = semantic_analyze(root, stdout);
    if (errors) {
        printf("Análise semântica concluída: %d %s; programa rejeitado.",
               errors, errors == 1 ? "erro" : "erros");
        ast_free(root);
        scanner_free(&scanner);
        free(source);
        return 4;
    }
    IrProgram ir;
    if (ir_generate(root, &ir, stderr) != 0) {
        ir_program_free(&ir);
        ast_free(root);
        scanner_free(&scanner);
        free(source);
        return 4;
    }
    ir_print(&ir, stdout);
    ir_program_free(&ir);
    ast_free(root);
    scanner_free(&scanner);
    free(source);
    return 0;
}

