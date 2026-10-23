/* Verify that C ir_generate rejects NULL, unannotated, and semantically invalid ASTs. */
#define main ir_cli_main
#include "../ir.c"
#undef main

static AstNode *parse_source(const char *src) {
    Scanner scanner;
    scanner_init(&scanner, src);
    scanner_scan_tokens(&scanner);
    if (scanner_has_errors(&scanner)) {
        scanner_free(&scanner);
        return NULL;
    }
    Parser parser;
    parser_init(&parser, scanner.tokens, scanner.tokens_len);
    parser.semantic_mode = 1;
    AstNode *root = parser_parse(&parser);
    scanner_free(&scanner);
    return root;
}

int main(void) {
    IrProgram ir;
    FILE *err = tmpfile();
    if (!err) return 1;

    /* 1. NULL AST must fail */
    if (ir_generate(NULL, &ir, err) == 0) {
        fclose(err);
        return 10;
    }

    /* 2. Unannotated AST (without semantic_analyze) must fail */
    AstNode *unannotated = parse_source("int main() { int x = 1; return x; }");
    if (!unannotated) {
        fclose(err);
        return 11;
    }
    if (ir_generate(unannotated, &ir, err) == 0) {
        ir_program_free(&ir);
        ast_free(unannotated);
        fclose(err);
        return 12;
    }
    ast_free(unannotated);

    /* 3. Semantically invalid AST must fail */
    AstNode *invalid_sem = parse_source("int main() { int x = 2.5; return ausente; }");
    if (!invalid_sem) {
        fclose(err);
        return 13;
    }
    int sem_errors = semantic_analyze(invalid_sem, err);
    if (sem_errors == 0 || ir_generate(invalid_sem, &ir, err) == 0) {
        ir_program_free(&ir);
        ast_free(invalid_sem);
        fclose(err);
        return 14;
    }
    ast_free(invalid_sem);

    /* 4. Valid annotated AST must succeed */
    AstNode *valid = parse_source("int main() { int x = 1; return x; }");
    if (!valid) {
        fclose(err);
        return 15;
    }
    if (semantic_analyze(valid, err) != 0 || ir_generate(valid, &ir, err) != 0) {
        ir_program_free(&ir);
        ast_free(valid);
        fclose(err);
        return 16;
    }
    ir_program_free(&ir);
    ast_free(valid);
    fclose(err);
    return 0;
}

