#include <stdio.h>
#include <stdlib.h>
#include "token.h"
#include "util.h"

Token token_create(TokenType type, const char *lexeme, int line, int column, const char *attr) {
    Token token = {type, xstrdup(lexeme ? lexeme : ""), line, column, xstrdup(attr)};
    return token;
}

void token_set_attr_int(Token *tok, long value) {
    char buffer[32];
    snprintf(buffer, sizeof(buffer), "%ld", value);
    free(tok->attribute);
    tok->attribute = xstrdup(buffer);
}

void token_set_attr_float(Token *tok, double value) {
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "%.17g", value);
    free(tok->attribute);
    tok->attribute = xstrdup(buffer);
}

void token_set_attr_string(Token *tok, const char *value) {
    free(tok->attribute);
    tok->attribute = xstrdup(value);
}

void token_free(Token *tok) {
    free(tok->lexeme);
    free(tok->attribute);
    tok->lexeme = NULL;
    tok->attribute = NULL;
}
