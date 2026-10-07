#ifndef AST_H
#define AST_H

#include <stddef.h>

typedef enum {
    AST_PROGRAM, AST_FUNCTION, AST_BLOCK, AST_VAR, AST_ID, AST_LIT, AST_UNARY,
    AST_BINARY, AST_ASSIGN, AST_CALL, AST_INDEX, AST_EXPR_STMT, AST_IF,
    AST_WHILE, AST_FOR, AST_RETURN, AST_PRINT, AST_READ, AST_BREAK,
    AST_CONTINUE, AST_NULL
} AstKind;

typedef struct AstNode {
    /* Metadata is excluded from S-expression serialization. */
    int line, column;
    int declaration_line, declaration_column;
    char *source_text;
    /* Semantic annotations: borrowed declaration/size links and static types. */
    const char *semantic_type;
    const char *coercion_type;
    const char *chain_coercion_type;
    const char *semantic_category;
    int semantic_scope;
    struct AstNode *resolved_declaration;
    struct AstNode *array_dimension;
    struct AstNode **parameters;
    size_t parameter_count;
    int is_array;
    AstKind kind;
    char *text;
    struct AstNode **children;
    size_t count;
    size_t capacity;
} AstNode;

AstNode *ast_new(AstKind kind, const char *text);
void ast_add(AstNode *node, AstNode *child);
char *ast_to_sexpr(const AstNode *node);
void ast_free(AstNode *node);

#endif
