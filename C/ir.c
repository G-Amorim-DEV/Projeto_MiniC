#include "ir.h"
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const AstNode *decl;
    char *ir_name;
} IrDeclEntry;

typedef struct {
    char *continue_label;
    char *break_label;
} IrLoopTarget;

typedef struct {
    IrProgram *program;
    int temp_counter;
    int label_counter;
    int in_function;
    IrLoopTarget *loops;
    size_t loop_count;
    size_t loop_capacity;
    IrDeclEntry *decls;
    size_t decl_count;
    size_t decl_capacity;
    char **global_names;
    size_t global_count;
    size_t global_capacity;
    char **seen_names;
    size_t seen_count;
    size_t seen_capacity;
    char **reserved_names;
    size_t reserved_count;
    size_t reserved_capacity;
} IrContext;

static char *ir_extract_decl_type(const AstNode *n) {
    const char *space = strchr(n->text, ' ');
    size_t len = space ? (size_t)(space - n->text) : strlen(n->text);
    char *res = xmalloc(len + 3);
    memcpy(res, n->text, len);
    res[len] = '\0';
    if (n->is_array) {
        memcpy(res + len, "[]", 3);
    }
    return res;
}

static char *ir_extract_decl_name(const AstNode *n) {
    const char *start = strchr(n->text, ' ');
    start = start ? start + 1 : n->text;
    const char *end = strchr(start, '(');
    size_t len = end ? (size_t)(end - start) : strlen(start);
    char *res = xmalloc(len + 1);
    memcpy(res, start, len);
    res[len] = '\0';
    return res;
}

void ir_program_init(IrProgram *program) {
    program->items = NULL;
    program->count = 0;
    program->capacity = 0;
}

void ir_program_free(IrProgram *program) {
    if (!program) return;
    for (size_t i = 0; i < program->count; ++i) {
        free(program->items[i].op);
        free(program->items[i].dest);
        free(program->items[i].arg1);
        free(program->items[i].arg2);
    }
    free(program->items);
    program->items = NULL;
    program->count = 0;
    program->capacity = 0;
}

static void ir_emit(
    IrContext *ctx,
    IrOpKind kind,
    const char *op,
    const char *dest,
    const char *arg1,
    const char *arg2,
    int in_function
) {
    if (ctx->program->count == ctx->program->capacity) {
        ctx->program->capacity = ctx->program->capacity ? ctx->program->capacity * 2 : 16;
        ctx->program->items = xrealloc(
            ctx->program->items,
            ctx->program->capacity * sizeof(*ctx->program->items)
        );
    }
    IrInstruction *inst = &ctx->program->items[ctx->program->count++];
    inst->kind = kind;
    inst->op = op ? xstrdup(op) : NULL;
    inst->dest = dest ? xstrdup(dest) : NULL;
    inst->arg1 = arg1 ? xstrdup(arg1) : NULL;
    inst->arg2 = arg2 ? xstrdup(arg2) : NULL;
    inst->in_function = in_function;
}

static int ir_name_in_list(char **list, size_t count, const char *name) {
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(list[i], name) == 0) return 1;
    }
    return 0;
}

static void ir_add_to_list(char ***list, size_t *count, size_t *cap, const char *name) {
    if (ir_name_in_list(*list, *count, name)) return;
    if (*count == *cap) {
        *cap = *cap ? *cap * 2 : 8;
        *list = xrealloc(*list, *cap * sizeof(**list));
    }
    (*list)[(*count)++] = xstrdup(name);
}

static void ir_free_list(char **list, size_t count) {
    for (size_t i = 0; i < count; ++i) free(list[i]);
    free(list);
}

static void ir_collect_reserved_names(IrContext *ctx, const AstNode *node) {
    if (!node || node->kind == AST_NULL) return;
    if (node->kind == AST_FUNCTION || node->kind == AST_VAR) {
        char *raw_name = ir_extract_decl_name(node);
        ir_add_to_list(&ctx->reserved_names, &ctx->reserved_count, &ctx->reserved_capacity, raw_name);
        if (node->semantic_scope > 0) {
            int n = snprintf(NULL, 0, "%s$%d", raw_name, node->semantic_scope);
            char *scoped = xmalloc((size_t)n + 1);
            snprintf(scoped, (size_t)n + 1, "%s$%d", raw_name, node->semantic_scope);
            ir_add_to_list(&ctx->reserved_names, &ctx->reserved_count, &ctx->reserved_capacity, scoped);
            free(scoped);
        }
        free(raw_name);
    } else if (node->kind == AST_ID) {
        ir_add_to_list(&ctx->reserved_names, &ctx->reserved_count, &ctx->reserved_capacity, node->text);
    }
    for (size_t i = 0; i < node->parameter_count; ++i) {
        ir_collect_reserved_names(ctx, node->parameters[i]);
    }
    for (size_t i = 0; i < node->count; ++i) {
        ir_collect_reserved_names(ctx, node->children[i]);
    }
}

static char *ir_new_temp(IrContext *ctx) {
    for (;;) {
        ctx->temp_counter++;
        int n = snprintf(NULL, 0, "t%d", ctx->temp_counter);
        char *buf = xmalloc((size_t)n + 1);
        snprintf(buf, (size_t)n + 1, "t%d", ctx->temp_counter);
        if (!ir_name_in_list(ctx->reserved_names, ctx->reserved_count, buf)) {
            ir_add_to_list(&ctx->reserved_names, &ctx->reserved_count, &ctx->reserved_capacity, buf);
            return buf;
        }
        free(buf);
    }
}

static char *ir_new_label(IrContext *ctx) {
    for (;;) {
        ctx->label_counter++;
        int n = snprintf(NULL, 0, "L%d", ctx->label_counter);
        char *buf = xmalloc((size_t)n + 1);
        snprintf(buf, (size_t)n + 1, "L%d", ctx->label_counter);
        if (!ir_name_in_list(ctx->reserved_names, ctx->reserved_count, buf)) {
            ir_add_to_list(&ctx->reserved_names, &ctx->reserved_count, &ctx->reserved_capacity, buf);
            return buf;
        }
        free(buf);
    }
}

static void ir_reset_seen_to_globals(IrContext *ctx) {
    ir_free_list(ctx->seen_names, ctx->seen_count);
    ctx->seen_names = NULL;
    ctx->seen_count = 0;
    ctx->seen_capacity = 0;
    for (size_t i = 0; i < ctx->global_count; ++i) {
        ir_add_to_list(&ctx->seen_names, &ctx->seen_count, &ctx->seen_capacity, ctx->global_names[i]);
    }
}

static const char *ir_lookup_decl_name(const IrContext *ctx, const AstNode *decl) {
    for (size_t i = 0; i < ctx->decl_count; ++i) {
        if (ctx->decls[i].decl == decl) return ctx->decls[i].ir_name;
    }
    return NULL;
}

static const char *ir_set_decl_name(IrContext *ctx, const AstNode *decl, const char *ir_name) {
    for (size_t i = 0; i < ctx->decl_count; ++i) {
        if (ctx->decls[i].decl == decl) {
            free(ctx->decls[i].ir_name);
            ctx->decls[i].ir_name = xstrdup(ir_name);
            return ctx->decls[i].ir_name;
        }
    }
    if (ctx->decl_count == ctx->decl_capacity) {
        ctx->decl_capacity = ctx->decl_capacity ? ctx->decl_capacity * 2 : 16;
        ctx->decls = xrealloc(ctx->decls, ctx->decl_capacity * sizeof(*ctx->decls));
    }
    ctx->decls[ctx->decl_count].decl = decl;
    ctx->decls[ctx->decl_count].ir_name = xstrdup(ir_name);
    return ctx->decls[ctx->decl_count++].ir_name;
}

static const char *ir_register_scoped_decl(IrContext *ctx, const AstNode *decl) {
    char *raw_name = ir_extract_decl_name(decl);
    int scope = decl->semantic_scope >= 0 ? decl->semantic_scope : 0;
    const char *result = NULL;

    if (scope == 0) {
        ir_add_to_list(&ctx->global_names, &ctx->global_count, &ctx->global_capacity, raw_name);
        ir_add_to_list(&ctx->seen_names, &ctx->seen_count, &ctx->seen_capacity, raw_name);
        result = ir_set_decl_name(ctx, decl, raw_name);
    } else if (!ir_name_in_list(ctx->seen_names, ctx->seen_count, raw_name)) {
        ir_add_to_list(&ctx->seen_names, &ctx->seen_count, &ctx->seen_capacity, raw_name);
        result = ir_set_decl_name(ctx, decl, raw_name);
    } else {
        int n = snprintf(NULL, 0, "%s$%d", raw_name, scope);
        char *scoped = xmalloc((size_t)n + 1);
        snprintf(scoped, (size_t)n + 1, "%s$%d", raw_name, scope);
        result = ir_set_decl_name(ctx, decl, scoped);
        free(scoped);
    }
    free(raw_name);
    return result;
}

static char *ir_resolve_var_name(const IrContext *ctx, const AstNode *node) {
    const AstNode *decl = node->resolved_declaration;
    if (decl) {
        const char *mapped = ir_lookup_decl_name(ctx, decl);
        if (mapped) return xstrdup(mapped);
    }
    if (node->kind == AST_ID) return xstrdup(node->text);
    return xstrdup("");
}

static void ir_push_loop(IrContext *ctx, const char *continue_label, const char *break_label) {
    if (ctx->loop_count == ctx->loop_capacity) {
        ctx->loop_capacity = ctx->loop_capacity ? ctx->loop_capacity * 2 : 4;
        ctx->loops = xrealloc(ctx->loops, ctx->loop_capacity * sizeof(*ctx->loops));
    }
    ctx->loops[ctx->loop_count].continue_label = xstrdup(continue_label);
    ctx->loops[ctx->loop_count].break_label = xstrdup(break_label);
    ctx->loop_count++;
}

static void ir_pop_loop(IrContext *ctx) {
    if (!ctx->loop_count) return;
    ctx->loop_count--;
    free(ctx->loops[ctx->loop_count].continue_label);
    free(ctx->loops[ctx->loop_count].break_label);
}

static int ir_validate_node(
    const AstNode *node,
    int in_func,
    int loop_depth,
    int *annotated_count,
    FILE *err_stream
) {
    if (!node || node->kind == AST_NULL) return 0;

    if (node->kind == AST_FUNCTION || node->kind == AST_VAR ||
        (node->kind >= AST_ID && node->kind <= AST_INDEX)) {
        (*annotated_count)++;
        if (!node->semantic_type) {
            if (err_stream) {
                fprintf(err_stream, "Erro de IR: AST sem análise semântica na linha %d, coluna %d.\n",
                        node->line, node->column);
            }
            return 1;
        }
        if (strcmp(node->semantic_type, "<error>") == 0) {
            if (err_stream) {
                fprintf(err_stream, "Erro de IR: AST contém erro semântico na linha %d, coluna %d.\n",
                        node->line, node->column);
            }
            return 1;
        }
    }

    if (node->kind == AST_FUNCTION || node->kind == AST_VAR ||
        node->kind == AST_ID || node->kind == AST_CALL) {
        if (!node->resolved_declaration) {
            if (err_stream) {
                fprintf(err_stream, "Erro de IR: símbolo não resolvido na linha %d, coluna %d.\n",
                        node->line, node->column);
            }
            return 1;
        }
    }

    if (node->kind == AST_RETURN && !in_func) {
        if (err_stream) fprintf(err_stream, "Erro de IR: 'return' fora de função.\n");
        return 1;
    }
    if ((node->kind == AST_BREAK || node->kind == AST_CONTINUE) && loop_depth <= 0) {
        if (err_stream) fprintf(err_stream, "Erro de IR: 'break'/'continue' fora de laço.\n");
        return 1;
    }

    int next_in_func = in_func || (node->kind == AST_FUNCTION);
    for (size_t i = 0; i < node->parameter_count; ++i) {
        if (ir_validate_node(node->parameters[i], 1, 0, annotated_count, err_stream) != 0)
            return 1;
    }
    for (size_t i = 0; i < node->count; ++i) {
        int child_loop = loop_depth;
        if ((node->kind == AST_WHILE && i == 1) || (node->kind == AST_FOR && i == 3)) {
            child_loop = loop_depth + 1;
        }
        if (ir_validate_node(node->children[i], next_in_func, child_loop, annotated_count, err_stream) != 0)
            return 1;
    }
    return 0;
}

static int ir_validate_ast(const AstNode *program, FILE *err_stream) {
    if (!program || program->kind != AST_PROGRAM) {
        if (err_stream) fprintf(err_stream, "Erro de IR: nó raiz inválido (esperado AST_PROGRAM).\n");
        return 1;
    }
    if (program->count == 0) {
        if (err_stream) fprintf(err_stream, "Erro de IR: AST vazia.\n");
        return 1;
    }
    int annotated_count = 0;
    if (ir_validate_node(program, 0, 0, &annotated_count, err_stream) != 0) {
        return 1;
    }
    if (annotated_count == 0) {
        if (err_stream) fprintf(err_stream, "Erro de IR: AST sem anotações semânticas.\n");
        return 1;
    }
    return 0;
}

static char *ir_emit_expr(IrContext *ctx, const AstNode *node);
static char *ir_emit_assign(IrContext *ctx, const AstNode *node);
static void ir_emit_statement(IrContext *ctx, const AstNode *node);

static char *ir_emit_expr_raw(IrContext *ctx, const AstNode *node) {
    if (node->kind == AST_LIT) {
        if (node->source_text && node->source_text[0]) {
            return xstrdup(node->source_text);
        }
        const char *comma = strchr(node->text, ',');
        const char *val = comma ? comma + 1 : node->text;
        if (strncmp(node->text, "char,", 5) == 0 && val[0] != '\'') {
            int n = snprintf(NULL, 0, "'%s'", val);
            char *res = xmalloc((size_t)n + 1);
            snprintf(res, (size_t)n + 1, "'%s'", val);
            return res;
        }
        if (strncmp(node->text, "string,", 7) == 0 && val[0] != '"') {
            int n = snprintf(NULL, 0, "\"%s\"", val);
            char *res = xmalloc((size_t)n + 1);
            snprintf(res, (size_t)n + 1, "\"%s\"", val);
            return res;
        }
        return xstrdup(val);
    }

    if (node->kind == AST_ID) {
        return ir_resolve_var_name(ctx, node);
    }

    if (node->kind == AST_UNARY) {
        char *operand_val = ir_emit_expr(ctx, node->children[0]);
        char *temp = ir_new_temp(ctx);
        ir_emit(ctx, IR_UNARY, node->text, temp, operand_val, NULL, ctx->in_function);
        free(operand_val);
        return temp;
    }

    if (node->kind == AST_BINARY) {
        char *left_val = ir_emit_expr(ctx, node->children[0]);
        char *right_val = ir_emit_expr(ctx, node->children[1]);
        char *temp = ir_new_temp(ctx);
        ir_emit(ctx, IR_BINARY, node->text, temp, left_val, right_val, ctx->in_function);
        free(left_val);
        free(right_val);
        return temp;
    }

    if (node->kind == AST_INDEX) {
        char *arr_name = ir_resolve_var_name(ctx, node->children[0]);
        char *idx_val = ir_emit_expr(ctx, node->children[1]);
        char *temp = ir_new_temp(ctx);
        ir_emit(ctx, IR_ARRAY_LOAD, NULL, temp, arr_name, idx_val, ctx->in_function);
        free(arr_name);
        free(idx_val);
        return temp;
    }

    if (node->kind == AST_CALL) {
        const AstNode *callee = node->children[0];
        size_t arg_count = node->count - 1;
        char **arg_vals = arg_count ? xmalloc(arg_count * sizeof(*arg_vals)) : NULL;
        for (size_t i = 0; i < arg_count; ++i) {
            arg_vals[i] = ir_emit_expr(ctx, node->children[i + 1]);
        }
        for (size_t i = 0; i < arg_count; ++i) {
            ir_emit(ctx, IR_ARG, NULL, NULL, arg_vals[i], NULL, ctx->in_function);
            free(arg_vals[i]);
        }
        free(arg_vals);

        int n = snprintf(NULL, 0, "%zu", arg_count);
        char *arity_str = xmalloc((size_t)n + 1);
        snprintf(arity_str, (size_t)n + 1, "%zu", arg_count);

        if (node->semantic_type && strcmp(node->semantic_type, "void") == 0) {
            ir_emit(ctx, IR_CALL, NULL, NULL, callee->text, arity_str, ctx->in_function);
            free(arity_str);
            return xstrdup("");
        }
        char *temp = ir_new_temp(ctx);
        ir_emit(ctx, IR_CALL, NULL, temp, callee->text, arity_str, ctx->in_function);
        free(arity_str);
        return temp;
    }

    if (node->kind == AST_ASSIGN) {
        return ir_emit_assign(ctx, node);
    }

    return xstrdup("");
}

static char *ir_emit_expr(IrContext *ctx, const AstNode *node) {
    char *val = ir_emit_expr_raw(ctx, node);
    if (node->coercion_type && strcmp(node->coercion_type, "float") == 0) {
        char *temp = ir_new_temp(ctx);
        ir_emit(ctx, IR_UNARY, "int2float", temp, val, NULL, ctx->in_function);
        free(val);
        return temp;
    }
    return val;
}

static char *ir_emit_assign(IrContext *ctx, const AstNode *node) {
    const AstNode *target = node->children[0];
    const AstNode *value = node->children[1];
    char *arr_name = NULL;
    char *idx_val = NULL;
    char *var_name = NULL;
    int target_is_index = (target->kind == AST_INDEX);

    if (target_is_index) {
        arr_name = ir_resolve_var_name(ctx, target->children[0]);
        idx_val = ir_emit_expr(ctx, target->children[1]);
    } else {
        var_name = ir_resolve_var_name(ctx, target);
    }

    char *rhs_val = NULL;
    if (value->kind == AST_ASSIGN) {
        rhs_val = ir_emit_assign(ctx, value);
        if (value->chain_coercion_type && strcmp(value->chain_coercion_type, "float") == 0) {
            char *coerced = ir_new_temp(ctx);
            ir_emit(ctx, IR_UNARY, "int2float", coerced, rhs_val, NULL, ctx->in_function);
            free(rhs_val);
            rhs_val = coerced;
        }
    } else {
        rhs_val = ir_emit_expr(ctx, value);
    }

    if (target_is_index) {
        ir_emit(ctx, IR_ARRAY_STORE, NULL, arr_name, idx_val, rhs_val, ctx->in_function);
        free(arr_name);
        free(idx_val);
        return rhs_val;
    } else {
        ir_emit(ctx, IR_COPY, NULL, var_name, rhs_val, NULL, ctx->in_function);
        free(rhs_val);
        return var_name;
    }
}

static void ir_emit_function(IrContext *ctx, const AstNode *func) {
    int prev_in_function = ctx->in_function;
    ir_reset_seen_to_globals(ctx);

    char *ret_type = ir_extract_decl_type(func);
    char *func_name = ir_extract_decl_name(func);

    ir_emit(ctx, IR_FUNC_BEGIN, NULL, func_name, ret_type, NULL, 0);
    free(ret_type);
    free(func_name);

    ctx->in_function = 1;

    for (size_t i = 0; i < func->parameter_count; ++i) {
        const AstNode *param = func->parameters[i];
        const char *ir_name = ir_register_scoped_decl(ctx, param);
        char *param_type = ir_extract_decl_type(param);
        ir_emit(ctx, IR_PARAM, NULL, ir_name, param_type, NULL, 1);
        free(param_type);
    }

    const AstNode *body = func->children[0];
    for (size_t i = 0; i < body->count; ++i) {
        ir_emit_statement(ctx, body->children[i]);
    }

    ctx->in_function = 0;
    ir_emit(ctx, IR_FUNC_END, NULL, NULL, NULL, NULL, 0);

    ctx->in_function = prev_in_function;
    ir_reset_seen_to_globals(ctx);
}

static void ir_emit_statement(IrContext *ctx, const AstNode *node) {
    if (!node || node->kind == AST_NULL) return;

    if (node->kind == AST_BLOCK) {
        for (size_t i = 0; i < node->count; ++i) {
            ir_emit_statement(ctx, node->children[i]);
        }
        return;
    }

    if (node->kind == AST_VAR) {
        int is_global = (node->semantic_scope == 0);
        const char *existing = ir_lookup_decl_name(ctx, node);
        const char *ir_name = (is_global && existing) ? existing : ir_register_scoped_decl(ctx, node);
        char *base_type = ir_extract_decl_type(node);
        IrOpKind decl_kind = is_global ? IR_GLOBAL : IR_LOCAL;
        int indent_flag = is_global ? 0 : ctx->in_function;

        if (node->count > 0 && node->children[0]) {
            char *size_val = ir_emit_expr(ctx, node->children[0]);
            ir_emit(ctx, decl_kind, NULL, ir_name, base_type, size_val, indent_flag);
            free(size_val);
        } else {
            ir_emit(ctx, decl_kind, NULL, ir_name, base_type, NULL, indent_flag);
            if (node->count > 1 && node->children[1]) {
                char *init_val = ir_emit_expr(ctx, node->children[1]);
                ir_emit(ctx, IR_COPY, NULL, ir_name, init_val, NULL, ctx->in_function);
                free(init_val);
            }
        }
        free(base_type);
        return;
    }

    if (node->kind == AST_EXPR_STMT) {
        const AstNode *expr = node->children[0];
        if (expr && expr->kind != AST_NULL) {
            char *val = (expr->kind == AST_ASSIGN)
                ? ir_emit_assign(ctx, expr)
                : ir_emit_expr(ctx, expr);
            free(val);
        }
        return;
    }

    if (node->kind == AST_IF) {
        const AstNode *cond = node->children[0];
        const AstNode *then_b = node->children[1];
        const AstNode *else_b = node->children[2];
        if (!else_b || else_b->kind == AST_NULL) {
            char *end_label = ir_new_label(ctx);
            char *cond_val = ir_emit_expr(ctx, cond);
            ir_emit(ctx, IR_IF_FALSE, NULL, end_label, cond_val, NULL, ctx->in_function);
            free(cond_val);
            ir_emit_statement(ctx, then_b);
            ir_emit(ctx, IR_LABEL, NULL, end_label, NULL, NULL, ctx->in_function);
            free(end_label);
        } else {
            char *else_label = ir_new_label(ctx);
            char *end_label = ir_new_label(ctx);
            char *cond_val = ir_emit_expr(ctx, cond);
            ir_emit(ctx, IR_IF_FALSE, NULL, else_label, cond_val, NULL, ctx->in_function);
            free(cond_val);
            ir_emit_statement(ctx, then_b);
            ir_emit(ctx, IR_GOTO, NULL, end_label, NULL, NULL, ctx->in_function);
            ir_emit(ctx, IR_LABEL, NULL, else_label, NULL, NULL, ctx->in_function);
            ir_emit_statement(ctx, else_b);
            ir_emit(ctx, IR_LABEL, NULL, end_label, NULL, NULL, ctx->in_function);
            free(else_label);
            free(end_label);
        }
        return;
    }

    if (node->kind == AST_WHILE) {
        char *start_label = ir_new_label(ctx);
        char *end_label = ir_new_label(ctx);
        ir_emit(ctx, IR_LABEL, NULL, start_label, NULL, NULL, ctx->in_function);
        char *cond_val = ir_emit_expr(ctx, node->children[0]);
        ir_emit(ctx, IR_IF_FALSE, NULL, end_label, cond_val, NULL, ctx->in_function);
        free(cond_val);
        ir_push_loop(ctx, start_label, end_label);
        ir_emit_statement(ctx, node->children[1]);
        ir_pop_loop(ctx);
        ir_emit(ctx, IR_GOTO, NULL, start_label, NULL, NULL, ctx->in_function);
        ir_emit(ctx, IR_LABEL, NULL, end_label, NULL, NULL, ctx->in_function);
        free(start_label);
        free(end_label);
        return;
    }

    if (node->kind == AST_FOR) {
        const AstNode *init = node->children[0];
        const AstNode *cond = node->children[1];
        const AstNode *inc = node->children[2];
        const AstNode *body = node->children[3];

        if (init && init->kind != AST_NULL) {
            char *v = (init->kind == AST_ASSIGN) ? ir_emit_assign(ctx, init) : ir_emit_expr(ctx, init);
            free(v);
        }
        char *start_label = ir_new_label(ctx);
        char *step_label = ir_new_label(ctx);
        char *end_label = ir_new_label(ctx);

        ir_emit(ctx, IR_LABEL, NULL, start_label, NULL, NULL, ctx->in_function);
        if (cond && cond->kind != AST_NULL) {
            char *cond_val = ir_emit_expr(ctx, cond);
            ir_emit(ctx, IR_IF_FALSE, NULL, end_label, cond_val, NULL, ctx->in_function);
            free(cond_val);
        }
        ir_push_loop(ctx, step_label, end_label);
        ir_emit_statement(ctx, body);
        ir_pop_loop(ctx);
        ir_emit(ctx, IR_LABEL, NULL, step_label, NULL, NULL, ctx->in_function);
        if (inc && inc->kind != AST_NULL) {
            char *v = (inc->kind == AST_ASSIGN) ? ir_emit_assign(ctx, inc) : ir_emit_expr(ctx, inc);
            free(v);
        }
        ir_emit(ctx, IR_GOTO, NULL, start_label, NULL, NULL, ctx->in_function);
        ir_emit(ctx, IR_LABEL, NULL, end_label, NULL, NULL, ctx->in_function);
        free(start_label);
        free(step_label);
        free(end_label);
        return;
    }

    if (node->kind == AST_RETURN) {
        const AstNode *val_node = node->children[0];
        if (val_node && val_node->kind != AST_NULL) {
            char *ret_val = ir_emit_expr(ctx, val_node);
            ir_emit(ctx, IR_RETURN, NULL, NULL, ret_val, NULL, ctx->in_function);
            free(ret_val);
        } else {
            ir_emit(ctx, IR_RETURN, NULL, NULL, NULL, NULL, ctx->in_function);
        }
        return;
    }

    if (node->kind == AST_BREAK) {
        if (ctx->loop_count > 0) {
            ir_emit(ctx, IR_GOTO, NULL, ctx->loops[ctx->loop_count - 1].break_label, NULL, NULL, ctx->in_function);
        }
        return;
    }

    if (node->kind == AST_CONTINUE) {
        if (ctx->loop_count > 0) {
            ir_emit(ctx, IR_GOTO, NULL, ctx->loops[ctx->loop_count - 1].continue_label, NULL, NULL, ctx->in_function);
        }
        return;
    }

    if (node->kind == AST_PRINT) {
        char *val = ir_emit_expr(ctx, node->children[0]);
        ir_emit(ctx, IR_PRINT, NULL, NULL, val, NULL, ctx->in_function);
        free(val);
        return;
    }

    if (node->kind == AST_READ) {
        const AstNode *target = node->children[0];
        if (target->kind == AST_INDEX) {
            char *arr_name = ir_resolve_var_name(ctx, target->children[0]);
            char *idx_val = ir_emit_expr(ctx, target->children[1]);
            ir_emit(ctx, IR_READ, NULL, arr_name, NULL, idx_val, ctx->in_function);
            free(arr_name);
            free(idx_val);
        } else {
            char *var_name = ir_resolve_var_name(ctx, target);
            ir_emit(ctx, IR_READ, NULL, var_name, NULL, NULL, ctx->in_function);
            free(var_name);
        }
        return;
    }
}

int ir_generate(const AstNode *ast_program, IrProgram *out_ir, FILE *err_stream) {
    if (!out_ir) return 1;
    ir_program_init(out_ir);
    if (ir_validate_ast(ast_program, err_stream) != 0) {
        return 1;
    }

    IrContext ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.program = out_ir;
    ir_collect_reserved_names(&ctx, ast_program);

    for (size_t i = 0; i < ast_program->count; ++i) {
        const AstNode *decl = ast_program->children[i];
        if (decl->kind == AST_VAR) {
            ir_register_scoped_decl(&ctx, decl);
        }
    }
    ir_reset_seen_to_globals(&ctx);

    for (size_t i = 0; i < ast_program->count; ++i) {
        const AstNode *decl = ast_program->children[i];
        if (decl->kind == AST_FUNCTION) {
            ir_emit_function(&ctx, decl);
        } else {
            ir_emit_statement(&ctx, decl);
        }
    }

    while (ctx.loop_count > 0) ir_pop_loop(&ctx);
    free(ctx.loops);
    for (size_t i = 0; i < ctx.decl_count; ++i) {
        free(ctx.decls[i].ir_name);
    }
    free(ctx.decls);
    ir_free_list(ctx.global_names, ctx.global_count);
    ir_free_list(ctx.seen_names, ctx.seen_count);
    ir_free_list(ctx.reserved_names, ctx.reserved_count);
    return 0;
}

static void ir_append_instruction(DynStr *out, const IrInstruction *inst) {
    const char *indent = inst->in_function ? "  " : "";
    switch (inst->kind) {
        case IR_GLOBAL:
            dynstr_push_str(out, "global ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->dest);
            if (inst->arg2) {
                dynstr_push_char(out, '[');
                dynstr_push_str(out, inst->arg2);
                dynstr_push_char(out, ']');
            }
            break;
        case IR_FUNC_BEGIN:
            dynstr_push_str(out, "func ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->dest);
            dynstr_push_char(out, ':');
            break;
        case IR_FUNC_END:
            dynstr_push_str(out, "endfunc");
            break;
        case IR_PARAM:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "param ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->dest);
            break;
        case IR_LOCAL:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "local ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->dest);
            if (inst->arg2) {
                dynstr_push_char(out, '[');
                dynstr_push_str(out, inst->arg2);
                dynstr_push_char(out, ']');
            }
            break;
        case IR_COPY:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_str(out, " = ");
            dynstr_push_str(out, inst->arg1);
            break;
        case IR_UNARY:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_str(out, " = ");
            dynstr_push_str(out, inst->op);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->arg1);
            break;
        case IR_BINARY:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_str(out, " = ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->op);
            dynstr_push_char(out, ' ');
            dynstr_push_str(out, inst->arg2);
            break;
        case IR_ARRAY_LOAD:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_str(out, " = ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_char(out, '[');
            dynstr_push_str(out, inst->arg2);
            dynstr_push_char(out, ']');
            break;
        case IR_ARRAY_STORE:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_char(out, '[');
            dynstr_push_str(out, inst->arg1);
            dynstr_push_str(out, "] = ");
            dynstr_push_str(out, inst->arg2);
            break;
        case IR_LABEL:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, inst->dest);
            dynstr_push_char(out, ':');
            break;
        case IR_GOTO:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "goto ");
            dynstr_push_str(out, inst->dest);
            break;
        case IR_IF_FALSE:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "if_false ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_str(out, " goto ");
            dynstr_push_str(out, inst->dest);
            break;
        case IR_ARG:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "arg ");
            dynstr_push_str(out, inst->arg1);
            break;
        case IR_CALL:
            dynstr_push_str(out, indent);
            if (inst->dest && inst->dest[0]) {
                dynstr_push_str(out, inst->dest);
                dynstr_push_str(out, " = ");
            }
            dynstr_push_str(out, "call ");
            dynstr_push_str(out, inst->arg1);
            dynstr_push_str(out, ", ");
            dynstr_push_str(out, inst->arg2);
            break;
        case IR_RETURN:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "return");
            if (inst->arg1 && inst->arg1[0]) {
                dynstr_push_char(out, ' ');
                dynstr_push_str(out, inst->arg1);
            }
            break;
        case IR_PRINT:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "print ");
            dynstr_push_str(out, inst->arg1);
            break;
        case IR_READ:
            dynstr_push_str(out, indent);
            dynstr_push_str(out, "read ");
            dynstr_push_str(out, inst->dest);
            if (inst->arg2 && inst->arg2[0]) {
                dynstr_push_char(out, '[');
                dynstr_push_str(out, inst->arg2);
                dynstr_push_char(out, ']');
            }
            break;
    }
}

char *ir_format(const IrProgram *program) {
    DynStr out;
    dynstr_init(&out);
    for (size_t i = 0; i < program->count; ++i) {
        if (i > 0) dynstr_push_char(&out, '\n');
        ir_append_instruction(&out, &program->items[i]);
    }
    return out.data;
}

void ir_print(const IrProgram *program, FILE *out_stream) {
    char *text = ir_format(program);
    fputs(text, out_stream);
    if (program->count > 0) fputc('\n', out_stream);
    free(text);
}

