#include "ast.h"
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

AstNode *ast_new(AstKind kind, const char *text) {
    AstNode *node = xmalloc(sizeof(*node));
    node->kind = kind; node->text = xstrdup(text ? text : "");
    node->count = 0; node->capacity = 4; node->children = xmalloc(4 * sizeof(*node->children));
    return node;
}
void ast_add(AstNode *node, AstNode *child) {
    if (node->count == node->capacity) { node->capacity *= 2; node->children = xrealloc(node->children, node->capacity * sizeof(*node->children)); }
    node->children[node->count++] = child;
}
void ast_free(AstNode *node) {
    if (!node) return;
    for (size_t i = 0; i < node->count; ++i) ast_free(node->children[i]);
    free(node->children); free(node->text); free(node);
}
static const char *name(AstKind kind) {
    static const char *names[] = {"Program", "Function", "Block", "VarDecl", "Id", "Lit", "Unary", "Binary", "Assign", "Call", "Index", "ExprStmt", "If", "While", "For", "Return", "Print", "Read", "Break", "Continue", "NULL"};
    return names[kind];
}
static void append_node(DynStr *out, const AstNode *node) {
    if (node->kind == AST_NULL) { dynstr_push_str(out, "NULL"); return; }
    dynstr_push_str(out, name(node->kind)); dynstr_push_char(out, '(');
    if (node->kind == AST_VAR) {
        dynstr_push_str(out, node->text);
        if (node->count && node->children[0]) { dynstr_push_char(out, '['); append_node(out, node->children[0]); dynstr_push_char(out, ']'); }
        if (node->count > 1 && node->children[1]) { dynstr_push_char(out, ','); append_node(out, node->children[1]); }
    } else if (node->kind == AST_FUNCTION) {
        dynstr_push_str(out, node->text);
        if (node->count) {
            dynstr_push_char(out, ' ');
            append_node(out, node->children[0]);
        }
    } else {
        if (node->text[0]) dynstr_push_str(out, node->text);
        for (size_t i = 0; i < node->count; ++i) {
            if (node->text[0] || i) dynstr_push_char(out, ',');
            append_node(out, node->children[i]);
        }
    }
    dynstr_push_char(out, ')');
}
char *ast_to_sexpr(const AstNode *node) { DynStr out; dynstr_init(&out); append_node(&out, node); return out.data; }
