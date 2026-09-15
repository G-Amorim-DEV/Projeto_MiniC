#ifndef PARSER_H
#define PARSER_H

#include "ast.h"
#include "token.h"
#include <stddef.h>

typedef struct {
    Token *tokens; size_t count; size_t current;
    int errors;
} Parser;

void parser_init(Parser *parser, Token *tokens, size_t count);
AstNode *parser_parse(Parser *parser);

#endif
