#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include "scanner.h"
#include "token_types.h"
#include "errors.h"
#include "util.h"

/* Função auxiliar para imprimir strings escapadas no padrão JSON */
static void print_json_escaped_string(FILE *stream, const char *str) {
    if (!str) {
        fputs("null", stream);
        return;
    }
    fputc('"', stream);
    for (size_t i = 0; str[i] != '\0'; i++) {
        switch (str[i]) {
            case '\\': fputs("\\\\", stream); break;
            case '"':  fputs("\\\"", stream); break;
            case '\n': fputs("\\n", stream); break;
            case '\r': fputs("\\r", stream); break;
            case '\t': fputs("\\t", stream); break;
            default:   fputc(str[i], stream); break;
        }
    }
    fputc('"', stream);
}

/* Serialização de um Token individual para formato JSONL */
static void print_tokens_jsonl(const Token *tokens, size_t count, FILE *stream) {
    for (size_t i = 0; i < count; i++) {
        const Token *t = &tokens[i];
        fprintf(stream, "{\"token\":\"%s\",\"lexeme\":", token_type_name(t->type));
        print_json_escaped_string(stream, t->lexeme);
        fprintf(stream, ",");
        
        if (t->attribute && strlen(t->attribute) > 0) {
            if (t->type == NUM_INT || t->type == NUM_FLOAT) {
                fprintf(stream, "\"attribute\":%s,", t->attribute);
            } else {
                fprintf(stream, "\"attribute\":");
                print_json_escaped_string(stream, t->attribute);
                fprintf(stream, ",");
            }
        } else {
            fprintf(stream, "\"attribute\":null,");
        }
        fprintf(stream, "\"line\":%d,\"column\":%d}\n", t->line, t->column);
    }
}

/* Serialização de erros léxicos para formato JSONL */
static void print_errors_jsonl(const LexicalError *errors, size_t count, FILE *stream) {
    for (size_t i = 0; i < count; i++) {
        const LexicalError *e = &errors[i];
        fprintf(stream, "{\"error\":\"%s\",\"lexeme\":", error_code_name(e->code));
        print_json_escaped_string(stream, e->lexeme);
        fprintf(stream, ",\"line\":%d,\"column\":%d}\n", e->line, e->column);
    }
}

int main(int argc, char *argv[]) {
    const char *filepath = NULL;
    bool modo_apenas_jsonl = true;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--jsonl") == 0) {
            modo_apenas_jsonl = true;
        } else if (argv[i][0] != '-' && filepath == NULL) {
            filepath = argv[i];
        }
    }

    if (!filepath) {
        fprintf(stderr, "Uso: ./scanner <arquivo.c | arquivo.minic> [--jsonl]\n");
        return 1;
    }

    char *source = read_file(filepath);
    if (!source) {
        fprintf(stderr, "Erro: Arquivo '%s' não encontrado.\n", filepath);
        return 1;
    }

    Scanner scanner;
    scanner_init(&scanner, source);
    scanner_scan_tokens(&scanner);

    /* Modo estrito: emite apenas o stream JSONL */
    if (modo_apenas_jsonl) {
        print_tokens_jsonl(scanner.tokens, scanner.tokens_len, stdout);
        if (scanner_has_errors(&scanner)) {
            print_errors_jsonl(scanner.errors, scanner.errors_len, stderr);
        }
        int code = scanner_has_errors(&scanner) ? 2 : 0;
        scanner_free(&scanner);
        free(source);
        return code;
    }

    /* Extrai apenas o nome do arquivo (basename) para o cabeçalho */
    const char *filename = strrchr(filepath, '/');
    if (!filename) filename = strrchr(filepath, '\\');
    filename = filename ? filename + 1 : filepath;

    /* Saída formatada igual ao Python */
    printf("================================================================================\n");
    printf("Análise Léxica - Arquivo: %s\n", filename);
    printf("================================================================================\n");
    printf("Tokens reconhecidos:\n");
    scanner_print_tokens(&scanner);
    printf("--------------------------------------------------------------------------------\n");
    printf("Diagnóstico:\n");
    scanner_print_errors(&scanner);

    printf("--------------------------------------------------------------------------------\n");
    printf("Saída JSONL (Tokens):\n");
    print_tokens_jsonl(scanner.tokens, scanner.tokens_len, stdout);

    if (scanner_has_errors(&scanner)) {
        printf("--------------------------------------------------------------------------------\n");
        printf("Saída JSONL (Erros):\n");
        print_errors_jsonl(scanner.errors, scanner.errors_len, stdout);
    }

    int exit_code = scanner_has_errors(&scanner) ? 2 : 0;
    scanner_free(&scanner);
    free(source);
    return exit_code;
}
