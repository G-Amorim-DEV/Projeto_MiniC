#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "errors.h"
#include "util.h"

const char *error_code_name(ErrorCode code) {
    switch (code) {
        case ERR_UNKNOWN_SYMBOL:
            return "UNKNOWN_SYMBOL";
        case ERR_INVALID_IDENTIFIER:
            return "INVALID_IDENTIFIER";
        case ERR_MALFORMED_REAL_LITERAL:
            return "MALFORMED_REAL_LITERAL";
        case ERR_UNTERMINATED_STRING_LITERAL:
            return "UNTERMINATED_STRING_LITERAL";
        case ERR_UNTERMINATED_BLOCK_COMMENT:
            return "UNTERMINATED_BLOCK_COMMENT";
        case ERR_UNTERMINATED_CHAR_LITERAL:
            return "UNTERMINATED_CHAR_LITERAL";
        default:
            return "ERRO_LEXICO";
    }
}

LexicalError error_create(ErrorCode code, const char *message, int line, int column, const char *lexeme) {
    LexicalError err;
    err.code = code;
    err.message = xstrdup(message);
    err.line = line;
    err.column = column;
    err.lexeme = xstrdup(lexeme ? lexeme : "");
    return err;
}

void error_free(LexicalError *err) {
    if (err->message) { free(err->message); err->message = NULL; }
    if (err->lexeme) { free(err->lexeme); err->lexeme = NULL; }
}

char *error_diagnostic(const LexicalError *err) {
    char origem[512];
    if (err->lexeme && err->lexeme[0] != '\0') {
        snprintf(origem, sizeof(origem), " proximo de '%s'", err->lexeme);
    } else {
        origem[0] = '\0';
    }

    size_t total_len = strlen(err->message) + strlen(origem) + 64;
    char *result = (char *)xmalloc(total_len);
    snprintf(result, total_len, "linha %d, coluna %d: %s%s",
             err->line, err->column, err->message, origem);
    return result;
}

LexicalError make_invalid_symbol_error(const char *ch, int line, int column) {
    char msg[256];
    snprintf(msg, sizeof(msg),
             "simbolo invalido '%s' (caractere nao reconhecido pela linguagem)", ch);
    return error_create(ERR_UNKNOWN_SYMBOL, msg, line, column, ch);
}

LexicalError make_invalid_identifier_error(const char *lexeme, int line, int column) {
    return error_create(ERR_INVALID_IDENTIFIER,
        "identificador invalido (nao pode comecar com digito)", line, column, lexeme);
}

LexicalError make_malformed_real_literal_error(const char *lexeme, int line, int column) {
    return error_create(ERR_MALFORMED_REAL_LITERAL,
        "literal real mal formado (faltou a parte fracionaria apos '.')", line, column, lexeme);
}

LexicalError make_unterminated_string_error(const char *partial, int line, int column) {
    return error_create(ERR_UNTERMINATED_STRING_LITERAL,
        "cadeia de caracteres nao terminada (faltando aspas de fechamento)", line, column, partial);
}

LexicalError make_unterminated_comment_error(const char *partial, int line, int column) {
    return error_create(ERR_UNTERMINATED_BLOCK_COMMENT,
        "comentario de bloco nao terminado (faltando '*/')", line, column, partial);
}

LexicalError make_unterminated_char_error(const char *partial, int line, int column) {
    return error_create(ERR_UNTERMINATED_CHAR_LITERAL,
        "literal de caractere mal formado (esperado aspa simples de fechamento)", line, column, partial);
}
