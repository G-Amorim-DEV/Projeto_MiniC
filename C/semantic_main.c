#include "ir.h"
#include "parser.h"
#include "scanner.h"
#include "semantic.h"
#include "util.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    int emit_ir = 0;
    const char *filepath = NULL;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--ir") == 0) {
            emit_ir = 1;
        } else if (argv[i][0] == '-') {
            fprintf(stderr, "Uso: ./minic [--ir] <arquivo.c | arquivo.minic>\n");
            return 1;
        } else if (!filepath) {
            filepath = argv[i];
        } else {
            fprintf(stderr, "Uso: ./minic [--ir] <arquivo.c | arquivo.minic>\n");
            return 1;
        }
    }
    if (!filepath) {
        fprintf(stderr, "Uso: ./minic [--ir] <arquivo.c | arquivo.minic>\n");
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
    if (emit_ir) {
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
    fputs("Análise semântica concluída: 0 erros; programa aceito.", stdout);
    ast_free(root);
    scanner_free(&scanner);
    free(source);
    return 0;
}
