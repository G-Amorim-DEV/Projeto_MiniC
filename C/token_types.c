#include <string.h>
#include <stddef.h>
#include "token_types.h"

const char *token_type_name(TokenType type) {
    switch (type) {
        /* Palavras Reservadas */
        case KW_BOOL: return "BOOL";
        case KW_INT: return "INT";
        case KW_FLOAT: return "FLOAT";
        case KW_CHAR: return "CHAR";
        case KW_DOUBLE: return "DOUBLE";
        case KW_VOID: return "VOID";
        case KW_TRUE: return "TRUE";
        case KW_FALSE: return "FALSE";
        case KW_IF: return "IF";
        case KW_ELSE: return "ELSE";
        case KW_WHILE: return "WHILE";
        case KW_FOR: return "FOR";
        case KW_RETURN: return "RETURN";
        case KW_BREAK: return "BREAK";
        case KW_CONTINUE: return "CONTINUE";
        case KW_PRINT: return "PRINT";
        case KW_READ: return "READ";

        /* Literais e Identificador */
        case ID: return "IDENT";
        case NUM_INT: return "INT_LIT";
        case NUM_FLOAT: return "FLOAT_LIT";
        case STRING: return "STRING_LIT";
        case CHAR_LITERAL: return "CHAR_LIT";

        /* Operadores Aritméticos e Pontuação */
        case PLUS: return "PLUS";
        case MINUS: return "MINUS";
        case STAR: return "STAR";
        case SLASH: return "SLASH";
        case PERCENT: return "PERCENT";
        case ASSIGN: return "ASSIGN";
        case EQ: return "EQ";
        case NEQ: return "NEQ";
        case LT: return "LT";
        case LE: return "LE";
        case GT: return "GT";
        case GE: return "GE";
        case AND: return "AND";
        case OR: return "OR";
        case NOT: return "NOT";
        case LPAREN: return "LPAREN";
        case RPAREN: return "RPAREN";
        case LBRACE: return "LBRACE";
        case RBRACE: return "RBRACE";
        case LBRACKET: return "LBRACKET";
        case RBRACKET: return "RBRACKET";
        case SEMI: return "SEMICOLON";
        case COMMA: return "COMMA";
        case DOT: return "DOT";

        /* Fim de Arquivo e Erros */
        case TOK_EOF: return "EOF";
        case TOK_ERROR: return "ERROR";
    }
    return "UNKNOWN";
}

typedef struct {
    const char *word;
    TokenType type;
} ReservedWord;

/* Tabela estática de palavras reservadas */
static const ReservedWord RESERVED_WORDS[] = {
    {"bool", KW_BOOL},
    {"int", KW_INT},
    {"float", KW_FLOAT},
    {"char", KW_CHAR},
    {"double", KW_DOUBLE},
    {"void", KW_VOID},
    {"true", KW_TRUE},
    {"false", KW_FALSE},
    {"if", KW_IF},
    {"else", KW_ELSE},
    {"while", KW_WHILE},
    {"for", KW_FOR},
    {"return", KW_RETURN},
    {"break", KW_BREAK},
    {"continue", KW_CONTINUE},
    {"print", KW_PRINT},
    {"read", KW_READ},
};

#define NUM_RESERVED_WORDS (sizeof(RESERVED_WORDS) / sizeof(RESERVED_WORDS[0]))

int is_reserved_word(const char *word, TokenType *out_type) {
    for (size_t i = 0; i < NUM_RESERVED_WORDS; i++) {
        if (strcmp(RESERVED_WORDS[i].word, word) == 0) {
            if (out_type) {
                *out_type = RESERVED_WORDS[i].type;
            }
            return 1;
        }
    }
    return 0;
}

TokenType lookup_reserved_word(const char *word) {
    TokenType t;
    if (is_reserved_word(word, &t)) {
        return t;
    }
    return ID;
}
