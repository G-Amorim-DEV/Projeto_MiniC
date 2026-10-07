/* Inspect persistent annotations after semantic scopes have been released. */
#define main semantic_cli_main
#include "../minic.c"
#undef main

static void dump_annotations(AstNode *node) {
    if (!node) return;
    if (node->kind >= AST_ID && node->kind <= AST_INDEX) {
        char *symbol = node->resolved_declaration ? sem_decl_name(node->resolved_declaration) : xstrdup("-");
        char *dimension = node->array_dimension ? sem_text(node->array_dimension) : xstrdup("-");
        printf("%d\t%d\t%s\t%s\t%s\t%s\t%d\t%s\t%s\n",
               node->line, node->column, name(node->kind),
               node->semantic_type ? node->semantic_type : "-",
               node->coercion_type ? node->coercion_type : "-", symbol,
               node->semantic_scope, dimension,
               node->chain_coercion_type ? node->chain_coercion_type : "-");
        free(symbol);
        free(dimension);
    }
    for (size_t i = 0; i < node->parameter_count; ++i) dump_annotations(node->parameters[i]);
    for (size_t i = 0; i < node->count; ++i) dump_annotations(node->children[i]);
}
int main(int argc, char **argv) {
    if (argc != 2) return 1;
    char *source = read_file(argv[1]);
    if (!source) return 1;
    Scanner scanner;
    scanner_init(&scanner, source);
    scanner_scan_tokens(&scanner);
    if (scanner_has_errors(&scanner)) { scanner_free(&scanner); free(source); return 2; }
    Parser parser;
    parser_init(&parser, scanner.tokens, scanner.tokens_len);
    parser.semantic_mode = 1;
    AstNode *root = parser_parse(&parser);
    if (!root) { scanner_free(&scanner); free(source); return 3; }
    char *before = ast_to_sexpr(root);
    FILE *diagnostics = tmpfile();
    if (!diagnostics) { free(before); ast_free(root); scanner_free(&scanner); free(source); return 1; }
    int errors = semantic_analyze(root, diagnostics);
    char *after = ast_to_sexpr(root);
    int stable = strcmp(before, after) == 0;
    free(after);
    free(before);
    if (stable) {
        dump_annotations(root);
        /* Analyzing the same AST again resets all borrowed links/coercions. */
        stable = semantic_analyze(root, diagnostics) == errors;
    }
    fclose(diagnostics);
    ast_free(root);
    scanner_free(&scanner);
    free(source);
    return stable ? 0 : 1;
}
