#include "scanner.h"
#include "token_types.h"
#include "errors.h"
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

void scanner_init(Scanner *sc, const char *source) {
    sc->source = source;
    sc->length = strlen(source);
    sc->pos = 0;
    sc->line = 1;
    sc->column = 1;

    sc->tokens_len = 0;
    sc->tokens_cap = 16;
    sc->tokens = (Token *)xmalloc(sc->tokens_cap * sizeof(Token));

    sc->errors_len = 0;
    sc->errors_cap = 8;
    sc->errors = (LexicalError *)xmalloc(sc->errors_cap * sizeof(LexicalError));
}

void scanner_free(Scanner *sc) {
    if (sc->tokens) {
        for (size_t i = 0; i < sc->tokens_len; i++) {
            token_free(&sc->tokens[i]);
        }
        free(sc->tokens);
        sc->tokens = NULL;
    }
    if (sc->errors) {
        for (size_t i = 0; i < sc->errors_len; i++) {
            error_free(&sc->errors[i]);
        }
        free(sc->errors);
        sc->errors = NULL;
    }
}

static void add_token(Scanner *sc, TokenType type, const char *lexeme, int line, int col, const char *attr) {
    if (sc->tokens_len >= sc->tokens_cap) {
        sc->tokens_cap *= 2;
        sc->tokens = (Token *)xrealloc(sc->tokens, sc->tokens_cap * sizeof(Token));
    }
    sc->tokens[sc->tokens_len++] = token_create(type, lexeme, line, col, attr);
}

static void add_error(Scanner *sc, LexicalError err) {
    if (sc->errors_len >= sc->errors_cap) {
        sc->errors_cap *= 2;
        sc->errors = (LexicalError *)xrealloc(sc->errors, sc->errors_cap * sizeof(LexicalError));
    }
    sc->errors[sc->errors_len++] = err;
}

static bool at_end(const Scanner *s) {
    return s->pos >= s->length;
}

static char peek(const Scanner *s, int offset) {
    size_t idx = s->pos + offset;
    return (idx < s->length) ? s->source[idx] : '\0';
}

static char advance(Scanner *s) {
    char ch = s->source[s->pos++];
    if (ch == '\n') {
        s->line++;
        s->column = 1;
    } else {
        s->column++;
    }
    return ch;
}

static bool match(Scanner *s, char expected) {
    if (peek(s, 0) == expected) {
        advance(s);
        return true;
    }
    return false;
}

static void skip_whitespace(Scanner *s) {
    while (!at_end(s) && (peek(s, 0) == ' ' || peek(s, 0) == '\t' || peek(s, 0) == '\r' || peek(s, 0) == '\n')) {
        advance(s);
    }
}

static void scan_identifier(Scanner *s, int line, int col, char first_char) {
    char buffer[256];
    int len = 0;
    buffer[len++] = first_char;

    while (!at_end(s) && (isalnum((unsigned char)peek(s, 0)) || peek(s, 0) == '_')) {
        if (len < 255) buffer[len++] = advance(s);
        else advance(s);
    }
    buffer[len] = '\0';

    TokenType type = lookup_reserved_word(buffer);
    const char *attr = (type == ID) ? buffer : NULL;
    add_token(s, type, buffer, line, col, attr);
}

static void scan_number(Scanner *s, int line, int col, char first_digit) {
    char buffer[256];
    int len = 0;
    buffer[len++] = first_digit;

    while (!at_end(s) && isdigit((unsigned char)peek(s, 0))) {
        if (len < 255) buffer[len++] = advance(s);
        else advance(s);
    }
    buffer[len] = '\0';

    /* Identificador inválido iniciado por dígito */
    if (!at_end(s) && (isalpha((unsigned char)peek(s, 0)) || peek(s, 0) == '_')) {
        char letters[256];
        int l_len = 0;
        int l_col = s->column;
        while (!at_end(s) && (isalnum((unsigned char)peek(s, 0)) || peek(s, 0) == '_')) {
            if (l_len < 255) letters[l_len++] = advance(s);
            else advance(s);
        }
        letters[l_len] = '\0';

        char full_inv[512];
        snprintf(full_inv, sizeof(full_inv), "%s%s", buffer, letters);
        add_error(s, make_invalid_identifier_error(full_inv, line, col));
        add_token(s, NUM_INT, buffer, line, col, buffer);
        add_token(s, ID, letters, line, l_col, letters);
        return;
    }

    /* Número real malformado ou válido */
    if (peek(s, 0) == '.') {
        if (!isdigit((unsigned char)peek(s, 1))) {
            int dot_col = s->column;
            advance(s);
            char malformed[260];
            snprintf(malformed, sizeof(malformed), "%s.", buffer);
            add_error(s, make_malformed_real_literal_error(malformed, line, col));
            add_token(s, NUM_INT, buffer, line, col, buffer);
            add_token(s, DOT, ".", line, dot_col, NULL);
            return;
        }

        if (len < 255) buffer[len++] = advance(s);
        while (!at_end(s) && isdigit((unsigned char)peek(s, 0))) {
            if (len < 255) buffer[len++] = advance(s);
            else advance(s);
        }
        buffer[len] = '\0';
        add_token(s, NUM_FLOAT, buffer, line, col, buffer);
        return;
    }

    add_token(s, NUM_INT, buffer, line, col, buffer);
}

static void scan_string(Scanner *s, int line, int col) {
    DynStr raw, value;
    dynstr_init(&raw);
    dynstr_init(&value);
    dynstr_push_char(&raw, '"');
    bool closed = false;

    while (!at_end(s)) {
        if (peek(s, 0) == '\n') break;
        if (peek(s, 0) == '"') {
            advance(s);
            dynstr_push_char(&raw, '"');
            closed = true;
            break;
        }
        char ch = advance(s);
        dynstr_push_char(&raw, ch);
        if (ch == '\\' && !at_end(s) && peek(s, 0) != '\n') {
            char escape = advance(s);
            dynstr_push_char(&raw, escape);
            if (strchr("nt\\\"'", escape) != NULL) {
                dynstr_push_char(&value, escape == 'n' ? '\n' : (escape == 't' ? '\t' : escape));
            } else {
                dynstr_push_char(&value, '\\');
                dynstr_push_char(&value, escape);
            }
        } else {
            dynstr_push_char(&value, ch);
        }
    }

    if (closed) {
        add_token(s, STRING, raw.data, line, col, value.data);
    } else {
        add_error(s, make_unterminated_string_error(raw.data, line, col));
        while (s->pos > 0 && strchr(") ;}]", s->source[s->pos - 1]) != NULL) {
            s->pos--;
            s->column--;
        }
    }
    dynstr_free(&raw);
    dynstr_free(&value);
}

static void scan_char(Scanner *s, int line, int col) {
    if (at_end(s) || peek(s, 0) == '\n') {
        add_error(s, make_unterminated_char_error("'", line, col));
        return;
    }

    char ch = advance(s);
    char raw[3] = {ch, '\0', '\0'};
    if (ch == '\\') {
        if (at_end(s) || peek(s, 0) == '\n') {
            add_error(s, make_unterminated_char_error("'\\", line, col));
            return;
        }
        char escape = advance(s);
        raw[1] = escape;
        if (strchr("nt\\\"'", escape) == NULL) {
            char bad[4] = {'\'', '\\', escape, '\0'};
            add_error(s, make_unterminated_char_error(bad, line, col));
            return;
        }
        ch = escape == 'n' ? '\n' : (escape == 't' ? '\t' : escape);
    }
    if (match(s, '\'')) {
        char lexeme[8];
        char attr[4] = {ch, '\0'};
        snprintf(lexeme, sizeof(lexeme), "'%s'", raw);
        add_token(s, CHAR_LITERAL, lexeme, line, col, attr);
    } else {
        char lexeme[8];
        snprintf(lexeme, sizeof(lexeme), "'%c", ch);
        add_error(s, make_unterminated_char_error(lexeme, line, col));
        if (peek(s, 0) == ';') advance(s);
    }
}

static void scan_token_item(Scanner *s) {
    int start_line = s->line;
    int start_col = s->column;
    char ch = advance(s);

    if (isalpha((unsigned char)ch) || ch == '_') {
        scan_identifier(s, start_line, start_col, ch);
    } else if (isdigit((unsigned char)ch)) {
        scan_number(s, start_line, start_col, ch);
    } else if (ch == '"') {
        scan_string(s, start_line, start_col);
    } else if (ch == '\'') {
        scan_char(s, start_line, start_col);
    } else if (ch == '/' && peek(s, 0) == '/') {
        advance(s);
        while (!at_end(s) && peek(s, 0) != '\n') advance(s);
    } else if (ch == '/' && peek(s, 0) == '*') {
        advance(s);
        int start_pos = (int)s->pos - 2;
        while (true) {
            if (at_end(s)) {
                size_t comm_len = s->pos - start_pos;
                char *comm_buf = (char *)xmalloc(comm_len + 1);
                strncpy(comm_buf, &s->source[start_pos], comm_len);
                comm_buf[comm_len] = '\0';

                add_error(s, make_unterminated_comment_error(comm_buf, start_line, start_col));
                free(comm_buf);
                return;
            }
            if (peek(s, 0) == '*' && peek(s, 1) == '/') {
                advance(s);
                advance(s);
                return;
            }
            advance(s);
        }
    } else {
        switch (ch) {
            case '+': add_token(s, PLUS, "+", start_line, start_col, NULL); break;
            case '-': add_token(s, MINUS, "-", start_line, start_col, NULL); break;
            case '*': add_token(s, STAR, "*", start_line, start_col, NULL); break;
            case '/': add_token(s, SLASH, "/", start_line, start_col, NULL); break;
            case '%': add_token(s, PERCENT, "%", start_line, start_col, NULL); break;
            case '.': add_token(s, DOT, ".", start_line, start_col, NULL); break;
            case ';': add_token(s, SEMI, ";", start_line, start_col, NULL); break;
            case ',': add_token(s, COMMA, ",", start_line, start_col, NULL); break;
            case '(': add_token(s, LPAREN, "(", start_line, start_col, NULL); break;
            case ')': add_token(s, RPAREN, ")", start_line, start_col, NULL); break;
            case '{': add_token(s, LBRACE, "{", start_line, start_col, NULL); break;
            case '}': add_token(s, RBRACE, "}", start_line, start_col, NULL); break;
            case '[': add_token(s, LBRACKET, "[", start_line, start_col, NULL); break;
            case ']': add_token(s, RBRACKET, "]", start_line, start_col, NULL); break;
            case '=':
                if (match(s, '=')) add_token(s, EQ, "==", start_line, start_col, NULL);
                else add_token(s, ASSIGN, "=", start_line, start_col, NULL);
                break;
            case '!':
                if (match(s, '=')) add_token(s, NEQ, "!=", start_line, start_col, NULL);
                else add_token(s, NOT, "!", start_line, start_col, NULL);
                break;
            case '<':
                if (match(s, '=')) add_token(s, LE, "<=", start_line, start_col, NULL);
                else add_token(s, LT, "<", start_line, start_col, NULL);
                break;
            case '>':
                if (match(s, '=')) add_token(s, GE, ">=", start_line, start_col, NULL);
                else add_token(s, GT, ">", start_line, start_col, NULL);
                break;
            case '&':
                if (match(s, '&')) add_token(s, AND, "&&", start_line, start_col, NULL);
                else {
                    char str[2] = {ch, '\0'};
                    add_error(s, make_invalid_symbol_error(str, start_line, start_col));
                }
                break;
            case '|':
                if (match(s, '|')) add_token(s, OR, "||", start_line, start_col, NULL);
                else {
                    char str[2] = {ch, '\0'};
                    add_error(s, make_invalid_symbol_error(str, start_line, start_col));
                }
                break;
            default: {
                char str[2] = {ch, '\0'};
                add_error(s, make_invalid_symbol_error(str, start_line, start_col));
                break;
            }
        }
    }
}

void scanner_scan_tokens(Scanner *s) {
    while (!at_end(s)) {
        skip_whitespace(s);
        if (at_end(s)) break;
        scan_token_item(s);
    }
    add_token(s, TOK_EOF, "", s->line, s->column, NULL);
}

bool scanner_has_errors(const Scanner *s) {
    return s->errors_len > 0;
}

void scanner_print_tokens(const Scanner *s) {
    printf("%-18s%-26s%-7s%-8s%s\n", "TIPO", "LEXEMA", "LINHA", "COLUNA", "ATRIBUTO");
    printf("---------------------------------------------------------------------------\n");
    for (size_t i = 0; i < s->tokens_len; i++) {
        const Token *t = &s->tokens[i];
        char repr[64];
        snprintf(repr, sizeof(repr), "'%s'", t->lexeme);
        if (strlen(repr) > 24) {
            repr[21] = '.';
            repr[22] = '.';
            repr[23] = '.';
            repr[24] = '\'';
            repr[25] = '\0';
        }
        printf("%-18s%-26s%-7d%-8d%s\n",
               token_type_name(t->type),
               repr,
               t->line,
               t->column,
               t->attribute ? t->attribute : "");
    }
}

void scanner_print_errors(const Scanner *s) {
    if (s->errors_len == 0) {
        printf("Nenhum erro léxico encontrado.\n");
        return;
    }
    printf("%zu erro(s) léxico(s) encontrado(s):\n", s->errors_len);
    for (size_t i = 0; i < s->errors_len; i++) {
        char *diag = error_diagnostic(&s->errors[i]);
        printf("  [ERRO LÉXICO] %s\n", diag);
        free(diag);
    }
}
