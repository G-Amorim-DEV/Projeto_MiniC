#ifndef SEMANTIC_H
#define SEMANTIC_H
#include "ast.h"
#include <stdio.h>
/* Annotate a parser-built AST; return the number of semantic errors. */
int semantic_analyze(AstNode *program, FILE *diagnostics);
#endif
