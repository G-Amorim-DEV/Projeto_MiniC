#include "parser.h"
#include "token_types.h"
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static Token *peek(Parser *p) { return &p->tokens[p->current]; }
static Token *previous(Parser *p) { return &p->tokens[p->current - 1]; }
static int at_end(Parser *p) { return peek(p)->type == TOK_EOF; }
static Token *advance_p(Parser *p) { if (!at_end(p)) p->current++; return previous(p); }
static int check(Parser *p, TokenType type) { return !at_end(p) && peek(p)->type == type; }
static int match(Parser *p, TokenType type) { if (check(p, type)) { advance_p(p); return 1; } return 0; }
static int is_type(TokenType type) { return type == KW_INT || type == KW_FLOAT || type == KW_BOOL || type == KW_CHAR; }
static void error_at(Parser *p, Token *token, const char *expected) {
    const char *found = token->type == TOK_EOF ? "EOF" : token->lexeme;
    fprintf(stderr, "Erro sintático na linha %d, coluna %d: esperado %s; encontrado '%s'\n", token->line, token->column, expected, found);
    p->errors++;
}
static Token *consume(Parser *p, TokenType type, const char *expected) {
    if (check(p, type)) return advance_p(p);
    error_at(p, peek(p), expected);
    return NULL;
}
static void synchronize(Parser *p) {
    /* Consome o token da falha para evitar repetir o mesmo ponto de
       sincronização indefinidamente. */
    if (!at_end(p)) advance_p(p);
    while (!at_end(p)) {
        if (p->current && previous(p)->type == SEMI) return;
        TokenType t = peek(p)->type;
        if (t == RBRACE || is_type(t) || t == KW_VOID || t == KW_IF || t == KW_WHILE || t == KW_FOR || t == KW_RETURN || t == KW_BREAK || t == KW_CONTINUE || t == KW_PRINT || t == KW_READ) return;
        advance_p(p);
    }
}
static AstNode *primary(Parser *p);
static AstNode *postfix(Parser *p);
static AstNode *unary(Parser *p);
static AstNode *assignment(Parser *p);
static AstNode *expression(Parser *p);
static AstNode *statement(Parser *p);
static AstNode *block(Parser *p);
static AstNode *declarator(Parser *p, const char *type_name, Token *name);
static AstNode *function_after(Parser *p, Token *type, Token *name);
static AstNode *expression(Parser *p);
static AstNode *statement(Parser *p);
static AstNode *block(Parser *p);
static AstNode *null_node(void) { return ast_new(AST_NULL, ""); }
static AstNode *literal_node(Token *token) {
    const char *type = "string";
    if (token->type == NUM_INT) type = "int";
    else if (token->type == NUM_FLOAT) type = "real";
    else if (token->type == KW_TRUE || token->type == KW_FALSE) type = "bool";
    else if (token->type == CHAR_LITERAL) type = "char";
    DynStr text;
    dynstr_init(&text);
    dynstr_push_str(&text, type);
    dynstr_push_char(&text, ',');
    dynstr_push_str(&text, (token->type == CHAR_LITERAL || token->type == STRING) && token->attribute ? token->attribute : token->lexeme);
    AstNode *node = ast_new(AST_LIT, text.data);
    dynstr_free(&text);
    return node;
}
static AstNode *left(Parser *p, AstNode *(*next)(Parser *), const TokenType *ops, size_t n) {
    AstNode *node = next(p);
    while (node) {
        int found = 0; for (size_t i = 0; i < n; ++i) if (match(p, ops[i])) { found = 1; break; }
        if (!found) break;
        Token *op = previous(p); AstNode *right = next(p);
        if (!right) { ast_free(node); return NULL; }
        AstNode *combined = ast_new(AST_BINARY, op->lexeme); combined->line=node->line; combined->column=node->column; ast_add(combined, node); ast_add(combined, right); node = combined;
    }
    return node;
}
static AstNode *primary_impl(Parser *p) {
    Token *t = peek(p);
    if (match(p, ID)) return ast_new(AST_ID, t->lexeme);
    if (match(p, NUM_INT) || match(p, NUM_FLOAT) || match(p, KW_TRUE) || match(p, KW_FALSE) || match(p, CHAR_LITERAL) || match(p, STRING)) return literal_node(t);
    if (match(p, LPAREN)) { AstNode *node = expression(p); if (!consume(p, RPAREN, "')' após expressão")) { ast_free(node); return NULL; } return node; }
    error_at(p, t, "expressão"); return NULL;
}
static AstNode *postfix_impl(Parser *p) {
    AstNode *node = primary(p);
    while (node) {
        if (match(p, LBRACKET)) {
            AstNode *index = expression(p);
            if (!index || !consume(p, RBRACKET, "']' após índice")) { ast_free(node); ast_free(index); return NULL; }
            AstNode *result = ast_new(AST_INDEX, ""); ast_add(result, node); ast_add(result, index); node = result;
        } else if (match(p, LPAREN)) {
            AstNode *call = ast_new(AST_CALL, ""); ast_add(call, node);
            if (!check(p, RPAREN)) {
                do { AstNode *argument = expression(p); if (!argument) { ast_free(call); return NULL; } ast_add(call, argument); } while (match(p, COMMA));
            }
            if (!consume(p, RPAREN, "')' após argumentos")) { ast_free(call); return NULL; } node = call;
        } else break;
    }
    return node;
}
static AstNode *unary_impl(Parser *p) { if (match(p, MINUS) || match(p, NOT)) { Token *op = previous(p); AstNode *operand = unary(p); if (!operand) return NULL; AstNode *node = ast_new(AST_UNARY, op->lexeme); ast_add(node, operand); return node; } return postfix(p); }
static AstNode *multiplicative(Parser *p) { TokenType ops[] = {STAR, SLASH, PERCENT}; return left(p, unary, ops, 3); }
static AstNode *additive(Parser *p) { TokenType ops[] = {PLUS, MINUS}; return left(p, multiplicative, ops, 2); }
static AstNode *relational(Parser *p) { TokenType ops[] = {LT, LE, GT, GE}; return left(p, additive, ops, 4); }
static AstNode *equality(Parser *p) { TokenType ops[] = {EQ, NEQ}; return left(p, relational, ops, 2); }
static AstNode *logical_and(Parser *p) { TokenType ops[] = {AND}; return left(p, equality, ops, 1); }
static AstNode *logical_or(Parser *p) { TokenType ops[] = {OR}; return left(p, logical_and, ops, 1); }
static AstNode *assignment_impl(Parser *p) {
    AstNode *node = logical_or(p); if (!node) return NULL;
    if (match(p, ASSIGN)) {
        Token *equals = previous(p); AstNode *value = assignment(p);
        if (!value) { ast_free(node); return NULL; }
        if (!p->semantic_mode && node->kind != AST_ID && node->kind != AST_INDEX) { error_at(p, equals, "localizável antes de '='"); ast_free(node); ast_free(value); return NULL; }
        AstNode *result = ast_new(AST_ASSIGN, ""); ast_add(result, node); ast_add(result, value); return result;
    } return node;
}
static AstNode *expression_impl(Parser *p) { return assignment(p); }
static AstNode *declarator_impl(Parser *p, const char *type_name, Token *name) {
    DynStr label; dynstr_init(&label); dynstr_push_str(&label, type_name); dynstr_push_char(&label, ' '); dynstr_push_str(&label, name->lexeme);
    AstNode *size = NULL, *init = NULL;
    if (match(p, LBRACKET)) { size = expression(p); if (!size || !consume(p, RBRACKET, "']' após tamanho do vetor")) { dynstr_free(&label); ast_free(size); return NULL; } }
    if (match(p, ASSIGN)) { init = expression(p); if (!init) { dynstr_free(&label); ast_free(size); return NULL; } }
    AstNode *node = ast_new(AST_VAR, label.data); dynstr_free(&label); ast_add(node, size); ast_add(node, init); return node;
}
static AstNode *local_declaration(Parser *p) {
    Token *type = advance_p(p); Token *name = consume(p, ID, "identificador na declaração local"); if (!name) return NULL;
    AstNode *first = declarator(p, type->lexeme, name); if (!first) return NULL;
    AstNode *container = ast_new(AST_BLOCK, ""); ast_add(container, first);
    while (match(p, COMMA)) { name = consume(p, ID, "identificador após ','"); AstNode *next = name ? declarator(p, type->lexeme, name) : NULL; if (!next) { ast_free(container); return NULL; } ast_add(container, next); }
    if (!consume(p, SEMI, "';' após declaração local")) { ast_free(container); return NULL; }
    return container;
}
static AstNode *if_statement(Parser *p) { if (!consume(p, LPAREN, "'(' após if")) return NULL; AstNode *cond = expression(p); if (!cond || !consume(p, RPAREN, "')' após condição")) { ast_free(cond); return NULL; } AstNode *then_node = statement(p); if (!then_node) { ast_free(cond); return NULL; } AstNode *node = ast_new(AST_IF, ""); ast_add(node, cond); ast_add(node, then_node); AstNode *other = null_node(); if (match(p, KW_ELSE)) { ast_free(other); other = statement(p); if (!other) { ast_free(node); return NULL; } } ast_add(node, other); return node; }
static AstNode *while_statement(Parser *p) { if (!consume(p, LPAREN, "'(' após while")) return NULL; AstNode *cond = expression(p); if (!cond || !consume(p, RPAREN, "')' após condição")) { ast_free(cond); return NULL; } AstNode *body = statement(p); if (!body) { ast_free(cond); return NULL; } AstNode *node = ast_new(AST_WHILE, ""); ast_add(node, cond); ast_add(node, body); return node; }
static AstNode *for_statement(Parser *p) { if (!consume(p, LPAREN, "'(' após for")) return NULL; AstNode *a = check(p, SEMI) ? null_node() : expression(p); if (!a || !consume(p, SEMI, "';' após inicialização do for")) { ast_free(a); return NULL; } AstNode *b = check(p, SEMI) ? null_node() : expression(p); if (!b || !consume(p, SEMI, "';' após condição do for")) { ast_free(a); ast_free(b); return NULL; } AstNode *c = check(p, RPAREN) ? null_node() : expression(p); if (!c || !consume(p, RPAREN, "')' após cláusulas do for")) { ast_free(a); ast_free(b); ast_free(c); return NULL; } AstNode *body = statement(p); if (!body) { ast_free(a); ast_free(b); ast_free(c); return NULL; } AstNode *node=ast_new(AST_FOR,""); ast_add(node,a);ast_add(node,b);ast_add(node,c);ast_add(node,body);return node; }
static AstNode *statement_impl(Parser *p) {
    if (check(p, LBRACE)) return block(p);
    if (match(p, KW_IF)) return if_statement(p);
    if (match(p, KW_WHILE)) return while_statement(p);
    if (match(p, KW_FOR)) return for_statement(p);
    if (match(p, KW_RETURN)) { AstNode *value = check(p, SEMI) ? null_node() : expression(p); if (!value || !consume(p, SEMI, "';' após return")) { ast_free(value); return NULL; } AstNode *node=ast_new(AST_RETURN,"");ast_add(node,value);return node; }
    if (match(p, KW_BREAK) || match(p, KW_CONTINUE)) { TokenType t=previous(p)->type; if (!consume(p, SEMI, "';' após comando")) return NULL; return ast_new(t==KW_BREAK?AST_BREAK:AST_CONTINUE,""); }
    if (match(p, KW_PRINT)) { if(!consume(p,LPAREN,"'(' após print"))return NULL; AstNode *value=expression(p); if(!value||!consume(p,RPAREN,"')' após argumento de print")||!consume(p,SEMI,"';' após print")){ast_free(value);return NULL;} AstNode*n=ast_new(AST_PRINT,"");ast_add(n,value);return n; }
    if (match(p, KW_READ)) { if(!consume(p,LPAREN,"'(' após read"))return NULL; AstNode *target=postfix(p); if(!target||!consume(p,RPAREN,"')' após argumento de read")||!consume(p,SEMI,"';' após read")){ast_free(target);return NULL;} if(target->kind!=AST_ID&&target->kind!=AST_INDEX){error_at(p,previous(p),"localizável como argumento de read");ast_free(target);return NULL;} AstNode*n=ast_new(AST_READ,"");ast_add(n,target);return n; }
    if (match(p, KW_ELSE)) { error_at(p, previous(p), "'if' antes de 'else'"); return NULL; }
    AstNode *value = check(p, SEMI) ? null_node() : expression(p); if(!value||!consume(p,SEMI,"';' após expressão")){ast_free(value);return NULL;} AstNode*n=ast_new(AST_EXPR_STMT,"");ast_add(n,value);return n;
}
static AstNode *block_impl(Parser *p) {
    if (!consume(p, LBRACE, "'{' para iniciar bloco")) return NULL;
    AstNode *node = ast_new(AST_BLOCK, "");
    while (!at_end(p) && !check(p,RBRACE)) {
        int local = is_type(peek(p)->type);
        AstNode *item = local ? local_declaration(p) : statement(p);
        if (!item) { synchronize(p); continue; }
        if (local) {
            for (size_t i = 0; i < item->count; ++i) ast_add(node, item->children[i]);
            free(item->children); free(item->text); free(item);
        } else ast_add(node, item);
    }
    if (!consume(p,RBRACE,"'}' para encerrar bloco")) { ast_free(node); return NULL; } return node;
}
static AstNode *function_after_impl(Parser *p, Token *type, Token *name) {
    if (!consume(p, LPAREN, "'(' após nome da função")) return NULL;
    AstNode *node = ast_new(AST_FUNCTION, "");
    node->declaration_line = type->line;
    node->declaration_column = type->column;
    DynStr signature;
    dynstr_init(&signature);
    dynstr_push_str(&signature, type->lexeme);
    dynstr_push_char(&signature, ' ');
    dynstr_push_str(&signature, name->lexeme);
    dynstr_push_char(&signature, '(');
    if (!check(p, RPAREN)) {
        do {
            Token *pt = peek(p);
            if (!is_type(pt->type)) {
                error_at(p, pt, "tipo do parâmetro");
                goto fail;
            }
            advance_p(p);
            Token *pn = consume(p, ID, "identificador do parâmetro");
            if (!pn) goto fail;
            if (node->parameter_count) dynstr_push_char(&signature, ',');
            DynStr label;
            dynstr_init(&label);
            dynstr_push_str(&label, pt->lexeme);
            dynstr_push_char(&label, ' ');
            dynstr_push_str(&label, pn->lexeme);
            AstNode *parameter = ast_new(AST_VAR, label.data);
            dynstr_push_str(&signature, label.data);
            dynstr_free(&label);
            parameter->line = pn->line;
            parameter->column = pn->column;
            node->parameters = xrealloc(node->parameters,
                (node->parameter_count + 1) * sizeof(*node->parameters));
            node->parameters[node->parameter_count++] = parameter;
            if (match(p, LBRACKET)) {
                if (!consume(p, RBRACKET, "']' no parâmetro")) goto fail;
                parameter->is_array = 1;
                dynstr_push_str(&signature, "[]");
            }
        } while (match(p, COMMA));
    }
    if (!consume(p, RPAREN, "')' após parâmetros")) goto fail;
    dynstr_push_char(&signature, ')');
    AstNode *body = block(p);
    if (!body) goto fail;
    free(node->text);
    node->text = signature.data;
    ast_add(node, body);
    return node;
fail:
    dynstr_free(&signature);
    ast_free(node);
    return NULL;
}

void parser_init(Parser *parser, Token *tokens, size_t count) { parser->tokens=tokens;parser->count=count;parser->current=0;parser->errors=0;parser->semantic_mode=0; }
AstNode *parser_parse(Parser *p) {
    AstNode *root = ast_new(AST_PROGRAM, "");
    while (!at_end(p)) {
        Token *type = peek(p);
        if (!is_type(type->type) && type->type != KW_VOID) {
            AstNode *top_level_statement = statement(p);
            if (top_level_statement) ast_add(root, top_level_statement);
            else synchronize(p);
            continue;
        }
        advance_p(p);
        Token *name = consume(p, ID, "identificador após tipo");
        if (!name) {
            synchronize(p);
            continue;
        }
        if (check(p, LPAREN)) {
            AstNode *function = function_after(p, type, name);
            if (!function) synchronize(p);
            else ast_add(root, function);
            continue;
        }
        if (type->type == KW_VOID) {
            error_at(p, name, "'(' após função void");
            synchronize(p);
            continue;
        }

        AstNode *declaration = declarator(p, type->lexeme, name);
        if (declaration) ast_add(root, declaration);
        while (declaration && match(p, COMMA)) {
            name = consume(p, ID, "identificador após ','");
            declaration = name ? declarator(p, type->lexeme, name) : NULL;
            if (declaration) ast_add(root, declaration);
        }
        if (!declaration || !consume(p, SEMI, "';' após declaração global"))
            synchronize(p);
    }
    if (p->errors) {
        ast_free(root);
        return NULL;
    }
    return root;
}


static void origin_node(Parser *p, AstNode *node, size_t start, const Token *origin) {
    if (!node) return;
    if (!node->source_text) {
        node->line=origin->line; node->column=origin->column;
        DynStr text; dynstr_init(&text);
        for (size_t i=start; i<p->current; ++i) {
            if(i!=start) dynstr_push_char(&text,' ');
            dynstr_push_str(&text,p->tokens[i].lexeme);
        }
        node->source_text=text.data;
    }
}
static AstNode *primary(Parser *p) {
    size_t start=p->current;
    AstNode *node=primary_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *postfix(Parser *p) {
    size_t start=p->current;
    AstNode *node=postfix_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *unary(Parser *p) {
    size_t start=p->current;
    AstNode *node=unary_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *assignment(Parser *p) {
    size_t start=p->current;
    AstNode *node=assignment_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *expression(Parser *p) {
    size_t start=p->current;
    AstNode *node=expression_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *statement(Parser *p) {
    size_t start=p->current;
    AstNode *node=statement_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *block(Parser *p) {
    size_t start=p->current;
    AstNode *node=block_impl(p);
    origin_node(p,node,start,&p->tokens[start]);
    return node;
}

static AstNode *declarator(Parser *p, const char *type_name, Token *name) {
    size_t start=p->current;
    AstNode *node=declarator_impl(p, type_name, name);
    origin_node(p,node,start,name);
    return node;
}

static AstNode *function_after(Parser *p, Token *type, Token *name) {
    size_t start = p->current;
    AstNode *node = function_after_impl(p, type, name);
    origin_node(p, node, start, name);
    return node;
}
