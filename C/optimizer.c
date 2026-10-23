#include "optimizer.h"
#include "util.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    IrInstruction *items;
    size_t count;
    size_t capacity;
} OptInstList;

static void opt_list_init(OptInstList *list) {
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
}

static IrInstruction opt_clone_inst(
    IrOpKind kind,
    const char *op,
    const char *dest,
    const char *arg1,
    const char *arg2,
    int in_function
) {
    IrInstruction inst;
    inst.kind = kind;
    inst.op = op ? xstrdup(op) : NULL;
    inst.dest = dest ? xstrdup(dest) : NULL;
    inst.arg1 = arg1 ? xstrdup(arg1) : NULL;
    inst.arg2 = arg2 ? xstrdup(arg2) : NULL;
    inst.in_function = in_function;
    return inst;
}

static IrInstruction opt_dup_inst(const IrInstruction *src) {
    return opt_clone_inst(src->kind, src->op, src->dest, src->arg1, src->arg2, src->in_function);
}

static void opt_free_inst(IrInstruction *inst) {
    if (!inst) return;
    free(inst->op);
    free(inst->dest);
    free(inst->arg1);
    free(inst->arg2);
    inst->op = NULL;
    inst->dest = NULL;
    inst->arg1 = NULL;
    inst->arg2 = NULL;
}

static void opt_list_push(OptInstList *list, IrInstruction inst) {
    if (list->count == list->capacity) {
        list->capacity = list->capacity ? list->capacity * 2 : 16;
        list->items = xrealloc(list->items, list->capacity * sizeof(*list->items));
    }
    list->items[list->count++] = inst;
}

static void opt_list_free(OptInstList *list) {
    if (!list) return;
    for (size_t i = 0; i < list->count; ++i) {
        opt_free_inst(&list->items[i]);
    }
    free(list->items);
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
}

static int opt_inst_equal(const IrInstruction *a, const IrInstruction *b) {
    if (a->kind != b->kind || a->in_function != b->in_function) return 0;
    if ((a->op == NULL) != (b->op == NULL)) return 0;
    if (a->op && strcmp(a->op, b->op) != 0) return 0;
    if ((a->dest == NULL) != (b->dest == NULL)) return 0;
    if (a->dest && strcmp(a->dest, b->dest) != 0) return 0;
    if ((a->arg1 == NULL) != (b->arg1 == NULL)) return 0;
    if (a->arg1 && strcmp(a->arg1, b->arg1) != 0) return 0;
    if ((a->arg2 == NULL) != (b->arg2 == NULL)) return 0;
    if (a->arg2 && strcmp(a->arg2, b->arg2) != 0) return 0;
    return 1;
}

static int opt_list_equal(const OptInstList *a, const OptInstList *b) {
    if (a->count != b->count) return 0;
    for (size_t i = 0; i < a->count; ++i) {
        if (!opt_inst_equal(&a->items[i], &b->items[i])) return 0;
    }
    return 1;
}

static int opt_is_temp(const char *s, int *out_num) {
    if (!s || s[0] != 't' || s[1] < '1' || s[1] > '9') return 0;
    for (size_t i = 1; s[i]; ++i) {
        if (!isdigit((unsigned char)s[i])) return 0;
    }
    if (out_num) *out_num = atoi(s + 1);
    return 1;
}

static int opt_is_int_lit(const char *s) {
    if (!s || !s[0]) return 0;
    size_t i = (s[0] == '-') ? 1 : 0;
    if (!s[i]) return 0;
    for (; s[i]; ++i) {
        if (!isdigit((unsigned char)s[i])) return 0;
    }
    return 1;
}

static int opt_is_float_lit(const char *s) {
    if (!s || !s[0]) return 0;
    size_t i = (s[0] == '-') ? 1 : 0;
    int digits_before = 0;
    while (s[i] && isdigit((unsigned char)s[i])) {
        digits_before++;
        i++;
    }
    if (!digits_before || s[i] != '.') return 0;
    i++;
    int digits_after = 0;
    while (s[i] && isdigit((unsigned char)s[i])) {
        digits_after++;
        i++;
    }
    return digits_after > 0 && s[i] == '\0';
}

static int opt_is_bool_lit(const char *s) {
    return s && (strcmp(s, "true") == 0 || strcmp(s, "false") == 0);
}

static int opt_is_num_or_bool_lit(const char *s) {
    return opt_is_int_lit(s) || opt_is_float_lit(s) || opt_is_bool_lit(s);
}

static int opt_is_user_var(const char *s) {
    if (!s || !s[0]) return 0;
    if (opt_is_temp(s, NULL) || opt_is_num_or_bool_lit(s)) return 0;
    if (s[0] == '"' || s[0] == '\'') return 0;
    return 1;
}

static int opt_str_in_list(char **list, size_t count, const char *s) {
    if (!s) return 0;
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(list[i], s) == 0) return 1;
    }
    return 0;
}

static void opt_str_list_add(char ***list, size_t *count, size_t *cap, const char *s) {
    if (!s || opt_str_in_list(*list, *count, s)) return;
    if (*count == *cap) {
        *cap = *cap ? *cap * 2 : 16;
        *list = xrealloc(*list, *cap * sizeof(**list));
    }
    (*list)[(*count)++] = xstrdup(s);
}

static void opt_str_list_free(char **list, size_t count) {
    for (size_t i = 0; i < count; ++i) free(list[i]);
    free(list);
}

static char *opt_format_float(double val) {
    char buf[64];
    snprintf(buf, sizeof(buf), "%.12g", val);
    if (!strchr(buf, '.') && !strchr(buf, 'e') && !strchr(buf, 'E')) {
        size_t len = strlen(buf);
        if (len + 2 < sizeof(buf)) {
            buf[len] = '.';
            buf[len + 1] = '0';
            buf[len + 2] = '\0';
        }
    }
    return xstrdup(buf);
}

static char *opt_eval_unary(const char *op, const char *arg) {
    if (!op || !arg) return NULL;
    if (strcmp(op, "-") == 0) {
        if (opt_is_int_lit(arg)) {
            long long v = -atoll(arg);
            char buf[64];
            snprintf(buf, sizeof(buf), "%lld", v);
            return xstrdup(buf);
        }
        if (opt_is_float_lit(arg)) {
            return opt_format_float(-strtod(arg, NULL));
        }
    } else if (strcmp(op, "!") == 0) {
        if (strcmp(arg, "true") == 0) return xstrdup("false");
        if (strcmp(arg, "false") == 0) return xstrdup("true");
    } else if (strcmp(op, "int2float") == 0) {
        if (opt_is_int_lit(arg)) {
            return opt_format_float((double)atoll(arg));
        }
        if (opt_is_float_lit(arg)) {
            return xstrdup(arg);
        }
    }
    return NULL;
}

static char *opt_eval_binary(const char *op, const char *left, const char *right) {
    if (!op || !left || !right) return NULL;
    if (opt_is_int_lit(left) && opt_is_int_lit(right)) {
        long long a = atoll(left);
        long long b = atoll(right);
        char buf[64];
        if (strcmp(op, "+") == 0) {
            snprintf(buf, sizeof(buf), "%lld", a + b);
            return xstrdup(buf);
        }
        if (strcmp(op, "-") == 0) {
            snprintf(buf, sizeof(buf), "%lld", a - b);
            return xstrdup(buf);
        }
        if (strcmp(op, "*") == 0) {
            snprintf(buf, sizeof(buf), "%lld", a * b);
            return xstrdup(buf);
        }
        if (strcmp(op, "/") == 0) {
            if (b == 0) return NULL;
            snprintf(buf, sizeof(buf), "%lld", a / b);
            return xstrdup(buf);
        }
        if (strcmp(op, "%") == 0) {
            if (b == 0) return NULL;
            snprintf(buf, sizeof(buf), "%lld", a % b);
            return xstrdup(buf);
        }
        if (strcmp(op, "<") == 0) return xstrdup(a < b ? "true" : "false");
        if (strcmp(op, "<=") == 0) return xstrdup(a <= b ? "true" : "false");
        if (strcmp(op, ">") == 0) return xstrdup(a > b ? "true" : "false");
        if (strcmp(op, ">=") == 0) return xstrdup(a >= b ? "true" : "false");
        if (strcmp(op, "==") == 0) return xstrdup(a == b ? "true" : "false");
        if (strcmp(op, "!=") == 0) return xstrdup(a != b ? "true" : "false");
        return NULL;
    }

    if ((opt_is_int_lit(left) || opt_is_float_lit(left)) &&
        (opt_is_int_lit(right) || opt_is_float_lit(right))) {
        double a = strtod(left, NULL);
        double b = strtod(right, NULL);
        if (strcmp(op, "+") == 0) return opt_format_float(a + b);
        if (strcmp(op, "-") == 0) return opt_format_float(a - b);
        if (strcmp(op, "*") == 0) return opt_format_float(a * b);
        if (strcmp(op, "/") == 0) {
            if (b == 0.0) return NULL;
            return opt_format_float(a / b);
        }
        if (strcmp(op, "<") == 0) return xstrdup(a < b ? "true" : "false");
        if (strcmp(op, "<=") == 0) return xstrdup(a <= b ? "true" : "false");
        if (strcmp(op, ">") == 0) return xstrdup(a > b ? "true" : "false");
        if (strcmp(op, ">=") == 0) return xstrdup(a >= b ? "true" : "false");
        if (strcmp(op, "==") == 0) return xstrdup(a == b ? "true" : "false");
        if (strcmp(op, "!=") == 0) return xstrdup(a != b ? "true" : "false");
        return NULL;
    }

    if (opt_is_bool_lit(left) && opt_is_bool_lit(right)) {
        int a = (strcmp(left, "true") == 0);
        int b = (strcmp(right, "true") == 0);
        if (strcmp(op, "&&") == 0) return xstrdup((a && b) ? "true" : "false");
        if (strcmp(op, "||") == 0) return xstrdup((a || b) ? "true" : "false");
        if (strcmp(op, "==") == 0) return xstrdup((a == b) ? "true" : "false");
        if (strcmp(op, "!=") == 0) return xstrdup((a != b) ? "true" : "false");
    }
    return NULL;
}

static const char *opt_written_name(const IrInstruction *inst) {
    if (inst->kind == IR_COPY || inst->kind == IR_UNARY ||
        inst->kind == IR_BINARY || inst->kind == IR_ARRAY_LOAD ||
        inst->kind == IR_CALL) {
        return inst->dest;
    }
    if (inst->kind == IR_READ && (!inst->arg2 || !inst->arg2[0])) {
        return inst->dest;
    }
    return NULL;
}

static OptInstList opt_eliminate_unreachable(const OptInstList *body) {
    OptInstList out;
    opt_list_init(&out);
    int unreachable = 0;
    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if (inst->kind == IR_LABEL) {
            unreachable = 0;
            opt_list_push(&out, opt_dup_inst(inst));
            continue;
        }
        if (unreachable) {
            if (inst->kind == IR_LOCAL) {
                opt_list_push(&out, opt_dup_inst(inst));
            }
            continue;
        }
        opt_list_push(&out, opt_dup_inst(inst));
        if (inst->kind == IR_RETURN || inst->kind == IR_GOTO) {
            unreachable = 1;
        }
    }
    return out;
}

static void opt_simplify_cfg(OptInstList *body) {
    int changed = 1;
    while (changed) {
        changed = 0;
        OptInstList after_term = opt_eliminate_unreachable(body);
        if (!opt_list_equal(&after_term, body)) {
            opt_list_free(body);
            *body = after_term;
            changed = 1;
        } else {
            opt_list_free(&after_term);
        }

        /* Remove GOTO L immediately followed by LABEL L */
        OptInstList filtered;
        opt_list_init(&filtered);
        for (size_t i = 0; i < body->count; ++i) {
            const IrInstruction *inst = &body->items[i];
            if (inst->kind == IR_GOTO && inst->dest &&
                i + 1 < body->count &&
                body->items[i + 1].kind == IR_LABEL &&
                body->items[i + 1].dest &&
                strcmp(inst->dest, body->items[i + 1].dest) == 0) {
                changed = 1;
                continue;
            }
            opt_list_push(&filtered, opt_dup_inst(inst));
        }
        opt_list_free(body);
        *body = filtered;

        /* Remove unused labels */
        char **targeted = NULL;
        size_t t_count = 0, t_cap = 0;
        for (size_t i = 0; i < body->count; ++i) {
            const IrInstruction *inst = &body->items[i];
            if ((inst->kind == IR_GOTO || inst->kind == IR_IF_FALSE) && inst->dest) {
                opt_str_list_add(&targeted, &t_count, &t_cap, inst->dest);
            }
        }

        OptInstList no_unused;
        opt_list_init(&no_unused);
        for (size_t i = 0; i < body->count; ++i) {
            const IrInstruction *inst = &body->items[i];
            if (inst->kind == IR_LABEL && inst->dest &&
                !opt_str_in_list(targeted, t_count, inst->dest)) {
                changed = 1;
                continue;
            }
            opt_list_push(&no_unused, opt_dup_inst(inst));
        }
        opt_str_list_free(targeted, t_count);
        opt_list_free(body);
        *body = no_unused;
    }
}

static void opt_simplify_algebraic(OptInstList *body) {
    OptInstList out;
    opt_list_init(&out);
    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if (inst->kind == IR_BINARY && inst->op && inst->dest && inst->arg1 && inst->arg2) {
            const char *op = inst->op;
            const char *a1 = inst->arg1;
            const char *a2 = inst->arg2;
            const char *rep = NULL;
            if (strcmp(op, "+") == 0) {
                if (strcmp(a2, "0") == 0 || strcmp(a2, "0.0") == 0) rep = a1;
                else if (strcmp(a1, "0") == 0 || strcmp(a1, "0.0") == 0) rep = a2;
            } else if (strcmp(op, "-") == 0) {
                if (strcmp(a2, "0") == 0 || strcmp(a2, "0.0") == 0) rep = a1;
                else if (strcmp(a1, a2) == 0 && !opt_is_float_lit(a1)) rep = "0";
            } else if (strcmp(op, "*") == 0) {
                if (strcmp(a2, "1") == 0 || strcmp(a2, "1.0") == 0) rep = a1;
                else if (strcmp(a1, "1") == 0 || strcmp(a1, "1.0") == 0) rep = a2;
                else if (strcmp(a2, "0") == 0 || strcmp(a1, "0") == 0) rep = "0";
            } else if (strcmp(op, "/") == 0) {
                if (strcmp(a2, "1") == 0 || strcmp(a2, "1.0") == 0) rep = a1;
            } else if (strcmp(op, "&&") == 0) {
                if (strcmp(a2, "true") == 0) rep = a1;
                else if (strcmp(a1, "true") == 0) rep = a2;
                else if (strcmp(a2, "false") == 0 || strcmp(a1, "false") == 0) rep = "false";
            } else if (strcmp(op, "||") == 0) {
                if (strcmp(a2, "false") == 0) rep = a1;
                else if (strcmp(a1, "false") == 0) rep = a2;
                else if (strcmp(a2, "true") == 0 || strcmp(a1, "true") == 0) rep = "true";
            }

            if (rep) {
                opt_list_push(&out, opt_clone_inst(IR_COPY, NULL, inst->dest, rep, NULL, inst->in_function));
                continue;
            }
        }
        opt_list_push(&out, opt_dup_inst(inst));
    }
    opt_list_free(body);
    *body = out;
}

typedef struct {
    char *name;
    char *val;
    int is_folded;
} ConstEntry;

static int const_find(ConstEntry *tab, size_t count, const char *name) {
    if (!name) return -1;
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(tab[i].name, name) == 0) return (int)i;
    }
    return -1;
}

static void const_set(ConstEntry **tab, size_t *count, size_t *cap, const char *name, const char *val, int folded) {
    int idx = const_find(*tab, *count, name);
    if (idx >= 0) {
        char *dup_val = xstrdup(val);
        free((*tab)[idx].val);
        (*tab)[idx].val = dup_val;
        (*tab)[idx].is_folded = folded;
        return;
    }
    if (*count == *cap) {
        *cap = *cap ? *cap * 2 : 16;
        *tab = xrealloc(*tab, *cap * sizeof(**tab));
    }
    (*tab)[*count].name = xstrdup(name);
    (*tab)[*count].val = xstrdup(val);
    (*tab)[*count].is_folded = folded;
    (*count)++;
}

static void const_remove(ConstEntry *tab, size_t *count, const char *name) {
    int idx = const_find(tab, *count, name);
    if (idx < 0) return;
    free(tab[idx].name);
    free(tab[idx].val);
    for (size_t i = (size_t)idx; i + 1 < *count; ++i) {
        tab[i] = tab[i + 1];
    }
    (*count)--;
}

static void const_clear(ConstEntry *tab, size_t *count) {
    for (size_t i = 0; i < *count; ++i) {
        free(tab[i].name);
        free(tab[i].val);
    }
    *count = 0;
}

static void opt_fold_constants_and_branches(OptInstList *body) {
    int branch_was_folded = 0;
    for (int round = 0; round < 4; ++round) {
        ConstEntry *consts = NULL;
        size_t c_count = 0, c_cap = 0;
        OptInstList next_body;
        opt_list_init(&next_body);
        int folded_branch_this_round = 0;

        for (size_t i = 0; i < body->count; ++i) {
            const IrInstruction *inst = &body->items[i];
            if (inst->kind == IR_LABEL || inst->kind == IR_GOTO || inst->kind == IR_RETURN) {
                if (inst->kind == IR_RETURN && inst->arg1) {
                    int idx = const_find(consts, c_count, inst->arg1);
                    if (idx >= 0 && consts[idx].is_folded) {
                        opt_list_push(&next_body, opt_clone_inst(
                            IR_RETURN, NULL, NULL, consts[idx].val, NULL, inst->in_function
                        ));
                        const_clear(consts, &c_count);
                        continue;
                    }
                }
                opt_list_push(&next_body, opt_dup_inst(inst));
                const_clear(consts, &c_count);
                continue;
            }

            if (inst->kind == IR_CALL) {
                opt_list_push(&next_body, opt_dup_inst(inst));
                const_clear(consts, &c_count);
                continue;
            }

            if (inst->kind == IR_COPY && inst->dest && inst->arg1) {
                int idx = const_find(consts, c_count, inst->arg1);
                if (idx >= 0) {
                    char *cval = xstrdup(consts[idx].val);
                    int cfold = consts[idx].is_folded;
                    const_set(&consts, &c_count, &c_cap, inst->dest, cval, cfold);
                    if (cfold) {
                        opt_list_push(&next_body, opt_clone_inst(
                            IR_COPY, NULL, inst->dest, cval, NULL, inst->in_function
                        ));
                    } else {
                        opt_list_push(&next_body, opt_dup_inst(inst));
                    }
                    free(cval);
                } else if (opt_is_num_or_bool_lit(inst->arg1)) {
                    const_set(&consts, &c_count, &c_cap, inst->dest, inst->arg1, branch_was_folded);
                    opt_list_push(&next_body, opt_dup_inst(inst));
                } else {
                    const_remove(consts, &c_count, inst->dest);
                    opt_list_push(&next_body, opt_dup_inst(inst));
                }
                continue;
            }

            if (inst->kind == IR_UNARY && inst->op && inst->dest && inst->arg1) {
                int idx = const_find(consts, c_count, inst->arg1);
                const char *v1 = (idx >= 0) ? consts[idx].val : inst->arg1;
                char *folded = opt_is_num_or_bool_lit(v1) ? opt_eval_unary(inst->op, v1) : NULL;
                if (folded) {
                    const_set(&consts, &c_count, &c_cap, inst->dest, folded, 1);
                    opt_list_push(&next_body, opt_clone_inst(
                        IR_COPY, NULL, inst->dest, folded, NULL, inst->in_function
                    ));
                    free(folded);
                } else {
                    const_remove(consts, &c_count, inst->dest);
                    opt_list_push(&next_body, opt_dup_inst(inst));
                }
                continue;
            }

            if (inst->kind == IR_BINARY && inst->op && inst->dest && inst->arg1 && inst->arg2) {
                int idx1 = const_find(consts, c_count, inst->arg1);
                int idx2 = const_find(consts, c_count, inst->arg2);
                int can_fold = opt_is_num_or_bool_lit(inst->arg1) ||
                               opt_is_num_or_bool_lit(inst->arg2) ||
                               (idx1 >= 0 && consts[idx1].is_folded) ||
                               (idx2 >= 0 && consts[idx2].is_folded);
                const char *v1 = (idx1 >= 0) ? consts[idx1].val : inst->arg1;
                const char *v2 = (idx2 >= 0) ? consts[idx2].val : inst->arg2;
                char *folded = (can_fold && opt_is_num_or_bool_lit(v1) && opt_is_num_or_bool_lit(v2))
                    ? opt_eval_binary(inst->op, v1, v2)
                    : NULL;
                if (folded) {
                    const_set(&consts, &c_count, &c_cap, inst->dest, folded, 1);
                    opt_list_push(&next_body, opt_clone_inst(
                        IR_COPY, NULL, inst->dest, folded, NULL, inst->in_function
                    ));
                    free(folded);
                } else {
                    const_remove(consts, &c_count, inst->dest);
                    opt_list_push(&next_body, opt_dup_inst(inst));
                }
                continue;
            }

            if (inst->kind == IR_IF_FALSE && inst->arg1 && inst->dest) {
                int idx = const_find(consts, c_count, inst->arg1);
                const char *cond_val = (idx >= 0) ? consts[idx].val : inst->arg1;
                if (strcmp(cond_val, "true") == 0) {
                    folded_branch_this_round = 1;
                    branch_was_folded = 1;
                    continue;
                }
                if (strcmp(cond_val, "false") == 0) {
                    folded_branch_this_round = 1;
                    branch_was_folded = 1;
                    opt_list_push(&next_body, opt_clone_inst(
                        IR_GOTO, NULL, inst->dest, NULL, NULL, inst->in_function
                    ));
                    const_clear(consts, &c_count);
                    continue;
                }
                opt_list_push(&next_body, opt_dup_inst(inst));
                const_clear(consts, &c_count);
                continue;
            }

            if ((inst->kind == IR_PRINT || inst->kind == IR_ARG) && inst->arg1) {
                int idx = const_find(consts, c_count, inst->arg1);
                if (idx >= 0 && consts[idx].is_folded) {
                    opt_list_push(&next_body, opt_clone_inst(
                        inst->kind, NULL, NULL, consts[idx].val, NULL, inst->in_function
                    ));
                    continue;
                }
                opt_list_push(&next_body, opt_dup_inst(inst));
                continue;
            }

            if ((inst->kind == IR_ARRAY_LOAD || inst->kind == IR_READ) && inst->dest) {
                const_remove(consts, &c_count, inst->dest);
                opt_list_push(&next_body, opt_dup_inst(inst));
                continue;
            }

            opt_list_push(&next_body, opt_dup_inst(inst));
        }

        const_clear(consts, &c_count);
        free(consts);

        opt_simplify_cfg(&next_body);
        int same = opt_list_equal(&next_body, body);
        opt_list_free(body);
        *body = next_body;
        if (same && !folded_branch_this_round) break;
    }
}

typedef struct {
    char *name;
    int count;
} WriteCount;

static int wc_get(WriteCount *list, size_t n, const char *name) {
    if (!name) return 0;
    for (size_t i = 0; i < n; ++i) {
        if (strcmp(list[i].name, name) == 0) return list[i].count;
    }
    return 0;
}

static void wc_inc(WriteCount **list, size_t *n, size_t *cap, const char *name) {
    if (!name) return;
    for (size_t i = 0; i < *n; ++i) {
        if (strcmp((*list)[i].name, name) == 0) {
            (*list)[i].count++;
            return;
        }
    }
    if (*n == *cap) {
        *cap = *cap ? *cap * 2 : 16;
        *list = xrealloc(*list, *cap * sizeof(**list));
    }
    (*list)[*n].name = xstrdup(name);
    (*list)[*n].count = 1;
    (*n)++;
}

static void wc_remove(WriteCount *list, size_t *n, const char *name) {
    if (!name) return;
    for (size_t i = 0; i < *n; ++i) {
        if (strcmp(list[i].name, name) == 0) {
            free(list[i].name);
            for (size_t j = i; j + 1 < *n; ++j) list[j] = list[j + 1];
            (*n)--;
            return;
        }
    }
}

static void wc_free(WriteCount *list, size_t n) {
    for (size_t i = 0; i < n; ++i) free(list[i].name);
    free(list);
}

static void opt_hoist_licm(OptInstList *body, char **globals, size_t global_count) {
    size_t idx = 0;
    while (idx < body->count) {
        if (body->items[idx].kind != IR_LABEL || !body->items[idx].dest) {
            idx++;
            continue;
        }
        const char *label_name = body->items[idx].dest;
        size_t back_idx = 0;
        int found_back = 0;
        for (size_t j = body->count; j > idx + 1; --j) {
            size_t k = j - 1;
            if (body->items[k].kind == IR_GOTO && body->items[k].dest &&
                strcmp(body->items[k].dest, label_name) == 0) {
                back_idx = k;
                found_back = 1;
                break;
            }
        }
        if (!found_back) {
            idx++;
            continue;
        }

        WriteCount *wcs = NULL;
        size_t wc_n = 0, wc_cap = 0;
        int has_call_or_array_store = 0;
        for (size_t k = idx + 1; k < back_idx; ++k) {
            const IrInstruction *ins = &body->items[k];
            if (ins->kind == IR_CALL || ins->kind == IR_ARRAY_STORE) {
                has_call_or_array_store = 1;
            }
            const char *w = opt_written_name(ins);
            if (w) wc_inc(&wcs, &wc_n, &wc_cap, w);
            if (ins->kind == IR_READ && ins->dest) wc_inc(&wcs, &wc_n, &wc_cap, ins->dest);
        }

        char *is_conditional = (char *)calloc(body->count, sizeof(char));
        for (size_t k = idx + 1; k < back_idx; ++k) {
            const IrInstruction *ins = &body->items[k];
            if ((ins->kind == IR_IF_FALSE || ins->kind == IR_GOTO) && ins->dest) {
                for (size_t m = idx + 1; m < back_idx; ++m) {
                    if (body->items[m].kind == IR_LABEL && body->items[m].dest &&
                        strcmp(body->items[m].dest, ins->dest) == 0) {
                        size_t start_m = (k < m) ? k : m;
                        size_t end_m = (k < m) ? m : k;
                        for (size_t p = start_m; p <= end_m; ++p) {
                            is_conditional[p] = 1;
                        }
                        break;
                    }
                }
            }
        }

        OptInstList hoisted, kept;
        opt_list_init(&hoisted);
        opt_list_init(&kept);

        for (size_t k = idx + 1; k < back_idx; ++k) {
            const IrInstruction *ins = &body->items[k];
            int can_hoist = 0;
            if (ins->kind == IR_BINARY && ins->op && ins->dest && ins->arg1 && ins->arg2 &&
                opt_is_temp(ins->dest, NULL) && wc_get(wcs, wc_n, ins->dest) == 1) {
                if (is_conditional[k]) {
                    can_hoist = 0;
                } else if (k + 1 < back_idx && body->items[k + 1].kind == IR_IF_FALSE &&
                    body->items[k + 1].arg1 && strcmp(body->items[k + 1].arg1, ins->dest) == 0) {
                    can_hoist = 0;
                } else if (strcmp(ins->op, "/") == 0 || strcmp(ins->op, "%") == 0) {
                    if (!(opt_is_int_lit(ins->arg2) || opt_is_float_lit(ins->arg2)) || atof(ins->arg2) == 0.0) {
                        can_hoist = 0;
                    } else if (wc_get(wcs, wc_n, ins->arg1) == 0 && wc_get(wcs, wc_n, ins->arg2) == 0) {
                        if (has_call_or_array_store &&
                            (opt_str_in_list(globals, global_count, ins->arg1) ||
                             opt_str_in_list(globals, global_count, ins->arg2))) {
                            can_hoist = 0;
                        } else {
                            can_hoist = 1;
                        }
                    }
                } else if (wc_get(wcs, wc_n, ins->arg1) == 0 && wc_get(wcs, wc_n, ins->arg2) == 0) {
                    if (has_call_or_array_store &&
                        (opt_str_in_list(globals, global_count, ins->arg1) ||
                         opt_str_in_list(globals, global_count, ins->arg2))) {
                        can_hoist = 0;
                    } else {
                        can_hoist = 1;
                    }
                }
            }
            if (can_hoist) {
                opt_list_push(&hoisted, opt_dup_inst(ins));
                wc_remove(wcs, &wc_n, ins->dest);
            } else {
                opt_list_push(&kept, opt_dup_inst(ins));
            }
        }
        free(is_conditional);
        wc_free(wcs, wc_n);

        if (hoisted.count > 0) {
            size_t h_count = hoisted.count;
            OptInstList rebuilt;
            opt_list_init(&rebuilt);
            for (size_t p = 0; p < idx; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));
            for (size_t p = 0; p < hoisted.count; ++p) opt_list_push(&rebuilt, opt_dup_inst(&hoisted.items[p]));
            opt_list_push(&rebuilt, opt_dup_inst(&body->items[idx]));
            for (size_t p = 0; p < kept.count; ++p) opt_list_push(&rebuilt, opt_dup_inst(&kept.items[p]));
            for (size_t p = back_idx; p < body->count; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));
            opt_list_free(&hoisted);
            opt_list_free(&kept);
            opt_list_free(body);
            *body = rebuilt;
            idx += h_count + 1;
        } else {
            opt_list_free(&hoisted);
            opt_list_free(&kept);
            idx++;
        }
    }
}

static void opt_reduce_induction_vars(OptInstList *body) {
    size_t idx = 0;
    while (idx < body->count) {
        if (body->items[idx].kind != IR_LABEL || !body->items[idx].dest) {
            idx++;
            continue;
        }
        const char *label_name = body->items[idx].dest;
        size_t back_idx = 0;
        int found_back = 0;
        for (size_t j = body->count; j > idx + 1; --j) {
            size_t k = j - 1;
            if (body->items[k].kind == IR_GOTO && body->items[k].dest &&
                strcmp(body->items[k].dest, label_name) == 0) {
                back_idx = k;
                found_back = 1;
                break;
            }
        }
        if (!found_back || back_idx - idx < 6) {
            idx++;
            continue;
        }

        int has_inner_branch = 0;
        for (size_t k = idx + 1; k < back_idx; ++k) {
            IrOpKind kind = body->items[k].kind;
            if (kind == IR_LABEL || kind == IR_GOTO || kind == IR_RETURN) {
                has_inner_branch = 1;
                break;
            }
            if (kind == IR_IF_FALSE && k > idx + 2) {
                has_inner_branch = 1;
                break;
            }
        }
        if (has_inner_branch) {
            idx++;
            continue;
        }

        const IrInstruction *inc_bin = &body->items[back_idx - 2];
        const IrInstruction *inc_copy = &body->items[back_idx - 1];
        if (!(inc_bin->kind == IR_BINARY && inc_bin->op && strcmp(inc_bin->op, "+") == 0 &&
              inc_bin->dest && opt_is_temp(inc_bin->dest, NULL) &&
              inc_bin->arg1 && opt_is_user_var(inc_bin->arg1) &&
              inc_bin->arg2 && opt_is_int_lit(inc_bin->arg2) &&
              inc_copy->kind == IR_COPY && inc_copy->dest && inc_copy->arg1 &&
              strcmp(inc_copy->dest, inc_bin->arg1) == 0 &&
              strcmp(inc_copy->arg1, inc_bin->dest) == 0)) {
            idx++;
            continue;
        }

        const char *iv = inc_bin->arg1;
        long long step_val = atoll(inc_bin->arg2);
        int found_iv_init = 0;
        long long iv_init_val = 0;
        for (size_t p = idx; p > 0; --p) {
            const IrInstruction *prev = &body->items[p - 1];
            if (prev->kind == IR_LABEL || prev->kind == IR_GOTO ||
                prev->kind == IR_IF_FALSE || prev->kind == IR_CALL || prev->kind == IR_RETURN) {
                break;
            }
            const char *w = opt_written_name(prev);
            if (w && strcmp(w, iv) == 0) {
                if (prev->kind == IR_COPY && prev->arg1 && opt_is_int_lit(prev->arg1)) {
                    iv_init_val = atoll(prev->arg1);
                    found_iv_init = 1;
                }
                break;
            }
        }
        if (!found_iv_init) {
            idx++;
            continue;
        }

        int iv_writes = 0;
        for (size_t k = idx + 1; k < back_idx; ++k) {
            const char *w = opt_written_name(&body->items[k]);
            if (w && strcmp(w, iv) == 0) iv_writes++;
        }
        if (iv_writes != 1) {
            idx++;
            continue;
        }

        size_t mul_pos = 0;
        int found_mul = 0;
        long long factor_val = 0;
        const char *derived_var = NULL;
        const char *mul_temp = NULL;

        for (size_t k = idx + 1; k + 2 < back_idx; ++k) {
            const IrInstruction *ins1 = &body->items[k];
            const IrInstruction *ins2 = &body->items[k + 1];
            if (ins1->kind == IR_BINARY && ins1->op && strcmp(ins1->op, "*") == 0 &&
                ins1->dest && opt_is_temp(ins1->dest, NULL) &&
                ins2->kind == IR_COPY && ins2->dest && opt_is_user_var(ins2->dest) &&
                ins2->arg1 && strcmp(ins2->arg1, ins1->dest) == 0) {
                long long fval = 0;
                if (ins1->arg1 && strcmp(ins1->arg1, iv) == 0 && ins1->arg2 && opt_is_int_lit(ins1->arg2)) {
                    fval = atoll(ins1->arg2);
                } else if (ins1->arg2 && strcmp(ins1->arg2, iv) == 0 && ins1->arg1 && opt_is_int_lit(ins1->arg1)) {
                    fval = atoll(ins1->arg1);
                } else {
                    continue;
                }

                const char *cand = ins2->dest;
                int cand_writes = 0;
                for (size_t m = idx + 1; m < back_idx; ++m) {
                    const char *w = opt_written_name(&body->items[m]);
                    if (w && strcmp(w, cand) == 0) cand_writes++;
                }
                int read_before = 0;
                for (size_t m = idx + 1; m < k; ++m) {
                    if ((body->items[m].arg1 && strcmp(body->items[m].arg1, cand) == 0) ||
                        (body->items[m].arg2 && strcmp(body->items[m].arg2, cand) == 0)) {
                        read_before = 1;
                        break;
                    }
                }
                if (cand_writes == 1 && !read_before) {
                    mul_pos = k;
                    found_mul = 1;
                    factor_val = fval;
                    derived_var = cand;
                    mul_temp = ins1->dest;
                    break;
                }
            }
        }

        if (!found_mul) {
            idx++;
            continue;
        }

        char init_buf[64], step_buf[64];
        snprintf(init_buf, sizeof(init_buf), "%lld", iv_init_val * factor_val);
        snprintf(step_buf, sizeof(step_buf), "%lld", step_val * factor_val);
        int in_fn = body->items[idx].in_function;
        char *dvar_dup = xstrdup(derived_var);
        char *mtemp_dup = xstrdup(mul_temp);

        OptInstList rebuilt;
        opt_list_init(&rebuilt);
        for (size_t p = 0; p < idx; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));
        opt_list_push(&rebuilt, opt_clone_inst(IR_COPY, NULL, dvar_dup, init_buf, NULL, in_fn));
        opt_list_push(&rebuilt, opt_dup_inst(&body->items[idx]));
        for (size_t p = idx + 1; p < mul_pos; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));
        for (size_t p = mul_pos + 2; p < back_idx; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));
        opt_list_push(&rebuilt, opt_clone_inst(IR_BINARY, "+", mtemp_dup, dvar_dup, step_buf, in_fn));
        opt_list_push(&rebuilt, opt_clone_inst(IR_COPY, NULL, dvar_dup, mtemp_dup, NULL, in_fn));
        for (size_t p = back_idx; p < body->count; ++p) opt_list_push(&rebuilt, opt_dup_inst(&body->items[p]));

        free(dvar_dup);
        free(mtemp_dup);
        opt_list_free(body);
        *body = rebuilt;
        idx += 2;
    }
}

typedef struct {
    IrOpKind kind;
    char *op;
    char *a1;
    char *a2;
    char *dest;
} AvailExpr;

static void avail_clear(AvailExpr *list, size_t *count) {
    for (size_t i = 0; i < *count; ++i) {
        free(list[i].op);
        free(list[i].a1);
        free(list[i].a2);
        free(list[i].dest);
    }
    *count = 0;
}

static void avail_invalidate(AvailExpr *list, size_t *count, const char *name) {
    if (!name) return;
    size_t i = 0;
    while (i < *count) {
        if (strcmp(list[i].dest, name) == 0 ||
            strcmp(list[i].a1, name) == 0 ||
            strcmp(list[i].a2, name) == 0) {
            free(list[i].op);
            free(list[i].a1);
            free(list[i].a2);
            free(list[i].dest);
            for (size_t j = i; j + 1 < *count; ++j) list[j] = list[j + 1];
            (*count)--;
        } else {
            i++;
        }
    }
}

static int opt_is_commutative(const char *op) {
    if (!op) return 0;
    return strcmp(op, "+") == 0 || strcmp(op, "*") == 0 ||
           strcmp(op, "==") == 0 || strcmp(op, "!=") == 0 ||
           strcmp(op, "&&") == 0 || strcmp(op, "||") == 0;
}

static int opt_cse(OptInstList *body) {
    OptInstList out;
    opt_list_init(&out);
    AvailExpr *avail = NULL;
    size_t a_count = 0, a_cap = 0;
    int replaced_any = 0;

    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if (inst->kind == IR_LABEL || inst->kind == IR_GOTO ||
            inst->kind == IR_IF_FALSE || inst->kind == IR_CALL || inst->kind == IR_RETURN) {
            avail_clear(avail, &a_count);
            opt_list_push(&out, opt_dup_inst(inst));
            continue;
        }

        if ((inst->kind == IR_BINARY || inst->kind == IR_UNARY) && inst->op && inst->dest) {
            const char *a1 = inst->arg1 ? inst->arg1 : "";
            const char *a2 = inst->arg2 ? inst->arg2 : "";
            if (inst->kind == IR_BINARY && opt_is_commutative(inst->op) && strcmp(a1, a2) > 0) {
                const char *tmp = a1;
                a1 = a2;
                a2 = tmp;
            }
            const char *existing = NULL;
            for (size_t k = 0; k < a_count; ++k) {
                if (avail[k].kind == inst->kind &&
                    strcmp(avail[k].op, inst->op) == 0 &&
                    strcmp(avail[k].a1, a1) == 0 &&
                    strcmp(avail[k].a2, a2) == 0) {
                    existing = avail[k].dest;
                    break;
                }
            }
            if (existing && strcmp(existing, inst->dest) != 0) {
                char *ex_dup = xstrdup(existing);
                avail_invalidate(avail, &a_count, inst->dest);
                opt_list_push(&out, opt_clone_inst(IR_COPY, NULL, inst->dest, ex_dup, NULL, inst->in_function));
                free(ex_dup);
                replaced_any = 1;
                continue;
            }

            avail_invalidate(avail, &a_count, inst->dest);
            if (opt_is_temp(inst->dest, NULL) &&
                strcmp(a1, inst->dest) != 0 && strcmp(a2, inst->dest) != 0) {
                if (a_count == a_cap) {
                    a_cap = a_cap ? a_cap * 2 : 16;
                    avail = xrealloc(avail, a_cap * sizeof(*avail));
                }
                avail[a_count].kind = inst->kind;
                avail[a_count].op = xstrdup(inst->op);
                avail[a_count].a1 = xstrdup(a1);
                avail[a_count].a2 = xstrdup(a2);
                avail[a_count].dest = xstrdup(inst->dest);
                a_count++;
            }
            opt_list_push(&out, opt_dup_inst(inst));
            continue;
        }

        const char *w = opt_written_name(inst);
        if (w) avail_invalidate(avail, &a_count, w);
        if (inst->kind == IR_READ && inst->dest) avail_invalidate(avail, &a_count, inst->dest);
        opt_list_push(&out, opt_dup_inst(inst));
    }

    avail_clear(avail, &a_count);
    free(avail);
    opt_list_free(body);
    *body = out;
    return replaced_any;
}

typedef struct {
    char *dest;
    char *src;
} CopyEntry;

static void copy_clear(CopyEntry *list, size_t *count) {
    for (size_t i = 0; i < *count; ++i) {
        free(list[i].dest);
        free(list[i].src);
    }
    *count = 0;
}

static void copy_invalidate(CopyEntry *list, size_t *count, const char *name) {
    if (!name) return;
    size_t i = 0;
    while (i < *count) {
        if (strcmp(list[i].dest, name) == 0 || strcmp(list[i].src, name) == 0) {
            free(list[i].dest);
            free(list[i].src);
            for (size_t j = i; j + 1 < *count; ++j) list[j] = list[j + 1];
            (*count)--;
        } else {
            i++;
        }
    }
}

static const char *copy_resolve(CopyEntry *list, size_t count, const char *val) {
    if (!val) return NULL;
    const char *curr = val;
    for (size_t step = 0; step < count + 1; ++step) {
        int found = 0;
        for (size_t i = 0; i < count; ++i) {
            if (strcmp(list[i].dest, curr) == 0) {
                curr = list[i].src;
                found = 1;
                break;
            }
        }
        if (!found) break;
    }
    return curr;
}

static void copy_set(CopyEntry **list, size_t *count, size_t *cap, const char *dest, const char *src) {
    if (*count == *cap) {
        *cap = *cap ? *cap * 2 : 16;
        *list = xrealloc(*list, *cap * sizeof(**list));
    }
    (*list)[*count].dest = xstrdup(dest);
    (*list)[*count].src = xstrdup(src);
    (*count)++;
}

static void opt_propagate_copies(OptInstList *body) {
    OptInstList out;
    opt_list_init(&out);
    CopyEntry *copies = NULL;
    size_t c_count = 0, c_cap = 0;

    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        IrOpKind kind = inst->kind;

        if (kind == IR_LABEL || kind == IR_GOTO || kind == IR_CALL) {
            copy_clear(copies, &c_count);
            opt_list_push(&out, opt_dup_inst(inst));
            continue;
        }

        if (kind == IR_IF_FALSE) {
            const char *r1 = copy_resolve(copies, c_count, inst->arg1);
            opt_list_push(&out, opt_clone_inst(IR_IF_FALSE, NULL, inst->dest, r1, NULL, inst->in_function));
            copy_clear(copies, &c_count);
            continue;
        }

        if (kind == IR_RETURN) {
            const char *r1 = copy_resolve(copies, c_count, inst->arg1);
            opt_list_push(&out, opt_clone_inst(IR_RETURN, NULL, NULL, r1, NULL, inst->in_function));
            copy_clear(copies, &c_count);
            continue;
        }

        if (kind == IR_COPY && inst->dest && inst->arg1) {
            char *src = xstrdup(copy_resolve(copies, c_count, inst->arg1));
            opt_list_push(&out, opt_clone_inst(IR_COPY, NULL, inst->dest, src, NULL, inst->in_function));
            copy_invalidate(copies, &c_count, inst->dest);
            if (strcmp(inst->dest, src) != 0) {
                if (opt_is_user_var(src) || (opt_is_temp(inst->dest, NULL) && opt_is_temp(src, NULL))) {
                    copy_set(&copies, &c_count, &c_cap, inst->dest, src);
                }
            }
            free(src);
            continue;
        }

        if (kind == IR_UNARY && inst->dest) {
            char *r1 = xstrdup(copy_resolve(copies, c_count, inst->arg1));
            opt_list_push(&out, opt_clone_inst(IR_UNARY, inst->op, inst->dest, r1, NULL, inst->in_function));
            copy_invalidate(copies, &c_count, inst->dest);
            free(r1);
            continue;
        }

        if (kind == IR_BINARY && inst->dest) {
            char *r1 = xstrdup(copy_resolve(copies, c_count, inst->arg1));
            char *r2 = xstrdup(copy_resolve(copies, c_count, inst->arg2));
            opt_list_push(&out, opt_clone_inst(IR_BINARY, inst->op, inst->dest, r1, r2, inst->in_function));
            copy_invalidate(copies, &c_count, inst->dest);
            free(r1);
            free(r2);
            continue;
        }

        if (kind == IR_ARRAY_LOAD && inst->dest) {
            char *r2 = xstrdup(copy_resolve(copies, c_count, inst->arg2));
            opt_list_push(&out, opt_clone_inst(IR_ARRAY_LOAD, NULL, inst->dest, inst->arg1, r2, inst->in_function));
            copy_invalidate(copies, &c_count, inst->dest);
            free(r2);
            continue;
        }

        if (kind == IR_ARRAY_STORE) {
            const char *r1 = copy_resolve(copies, c_count, inst->arg1);
            const char *r2 = copy_resolve(copies, c_count, inst->arg2);
            opt_list_push(&out, opt_clone_inst(IR_ARRAY_STORE, NULL, inst->dest, r1, r2, inst->in_function));
            continue;
        }

        if (kind == IR_PRINT || kind == IR_ARG) {
            const char *r1 = copy_resolve(copies, c_count, inst->arg1);
            opt_list_push(&out, opt_clone_inst(kind, NULL, NULL, r1, NULL, inst->in_function));
            continue;
        }

        if (kind == IR_READ && inst->dest) {
            char *r2 = inst->arg2 ? xstrdup(copy_resolve(copies, c_count, inst->arg2)) : NULL;
            copy_invalidate(copies, &c_count, inst->dest);
            opt_list_push(&out, opt_clone_inst(IR_READ, NULL, inst->dest, NULL, r2, inst->in_function));
            free(r2);
            continue;
        }

        opt_list_push(&out, opt_dup_inst(inst));
    }

    copy_clear(copies, &c_count);
    free(copies);
    opt_list_free(body);
    *body = out;
}

static void opt_collect_reads(const IrInstruction *inst, char ***reads, size_t *count, size_t *cap) {
    switch (inst->kind) {
        case IR_COPY:
        case IR_UNARY:
        case IR_IF_FALSE:
        case IR_ARG:
        case IR_RETURN:
        case IR_PRINT:
            if (inst->arg1) opt_str_list_add(reads, count, cap, inst->arg1);
            break;
        case IR_BINARY:
        case IR_ARRAY_LOAD:
            if (inst->arg1) opt_str_list_add(reads, count, cap, inst->arg1);
            if (inst->arg2) opt_str_list_add(reads, count, cap, inst->arg2);
            break;
        case IR_ARRAY_STORE:
            if (inst->dest) opt_str_list_add(reads, count, cap, inst->dest);
            if (inst->arg1) opt_str_list_add(reads, count, cap, inst->arg1);
            if (inst->arg2) opt_str_list_add(reads, count, cap, inst->arg2);
            break;
        case IR_READ:
            if (inst->dest) opt_str_list_add(reads, count, cap, inst->dest);
            if (inst->arg2) opt_str_list_add(reads, count, cap, inst->arg2);
            break;
        default:
            break;
    }
}

static void opt_eliminate_dead_stores(OptInstList *body, char **globals, size_t global_count) {
    int changed = 1;
    while (changed) {
        changed = 0;
        char **reads = NULL;
        size_t r_count = 0, r_cap = 0;
        for (size_t i = 0; i < body->count; ++i) {
            opt_collect_reads(&body->items[i], &reads, &r_count, &r_cap);
        }

        OptInstList next_body;
        opt_list_init(&next_body);
        for (size_t i = 0; i < body->count; ++i) {
            const IrInstruction *inst = &body->items[i];
            if (inst->kind == IR_COPY && inst->dest && inst->arg1 &&
                strcmp(inst->dest, inst->arg1) == 0) {
                changed = 1;
                continue;
            }
            if ((inst->kind == IR_COPY || inst->kind == IR_UNARY ||
                 inst->kind == IR_BINARY || inst->kind == IR_ARRAY_LOAD) && inst->dest) {
                if (!opt_str_in_list(reads, r_count, inst->dest) &&
                    !opt_str_in_list(globals, global_count, inst->dest)) {
                    changed = 1;
                    continue;
                }
            }
            opt_list_push(&next_body, opt_dup_inst(inst));
        }
        opt_str_list_free(reads, r_count);
        opt_list_free(body);
        *body = next_body;
    }

    char **referenced = NULL;
    size_t ref_count = 0, ref_cap = 0;
    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if (inst->kind == IR_LOCAL) continue;
        opt_collect_reads(inst, &referenced, &ref_count, &ref_cap);
        const char *w = opt_written_name(inst);
        if (w) opt_str_list_add(&referenced, &ref_count, &ref_cap, w);
        if (inst->kind == IR_READ && inst->dest) opt_str_list_add(&referenced, &ref_count, &ref_cap, inst->dest);
    }

    OptInstList final_body;
    opt_list_init(&final_body);
    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if (inst->kind == IR_LOCAL && !inst->arg2 && inst->dest) {
            if (!opt_str_in_list(referenced, ref_count, inst->dest)) {
                continue;
            }
        }
        opt_list_push(&final_body, opt_dup_inst(inst));
    }
    opt_str_list_free(referenced, ref_count);
    opt_list_free(body);
    *body = final_body;
}

static void opt_inspect_temp_or_var(
    const char *tok,
    char ***temps,
    size_t *t_count,
    size_t *t_cap,
    char ***reserved,
    size_t *r_count,
    size_t *r_cap
) {
    if (!tok || !tok[0]) return;
    if (opt_is_temp(tok, NULL)) {
        opt_str_list_add(temps, t_count, t_cap, tok);
    } else if (opt_is_user_var(tok)) {
        opt_str_list_add(reserved, r_count, r_cap, tok);
    }
}

static const char *opt_remap_tok(const char *tok, char **old_t, char **new_t, size_t count) {
    if (!tok) return NULL;
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(tok, old_t[i]) == 0) return new_t[i];
    }
    return tok;
}

static void opt_renumber_temps_if_needed(OptInstList *body) {
    char **temps = NULL;
    size_t t_count = 0, t_cap = 0;
    char **reserved = NULL;
    size_t r_count = 0, r_cap = 0;

    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        if ((inst->kind == IR_PARAM || inst->kind == IR_LOCAL) && inst->dest) {
            opt_str_list_add(&reserved, &r_count, &r_cap, inst->dest);
            continue;
        }
        if (inst->kind != IR_LABEL && inst->kind != IR_GOTO &&
            inst->kind != IR_IF_FALSE && inst->kind != IR_CALL) {
            opt_inspect_temp_or_var(inst->dest, &temps, &t_count, &t_cap, &reserved, &r_count, &r_cap);
        }
        opt_inspect_temp_or_var(inst->arg1, &temps, &t_count, &t_cap, &reserved, &r_count, &r_cap);
        opt_inspect_temp_or_var(inst->arg2, &temps, &t_count, &t_cap, &reserved, &r_count, &r_cap);
    }

    if (t_count == 0) {
        opt_str_list_free(temps, t_count);
        opt_str_list_free(reserved, r_count);
        return;
    }

    int max_idx = 0;
    for (size_t i = 0; i < t_count; ++i) {
        int num = 0;
        if (opt_is_temp(temps[i], &num) && num > max_idx) max_idx = num;
    }

    if ((int)t_count == max_idx) {
        opt_str_list_free(temps, t_count);
        opt_str_list_free(reserved, r_count);
        return;
    }

    char **new_temps = xmalloc(t_count * sizeof(*new_temps));
    int counter = 0;
    for (size_t i = 0; i < t_count; ++i) {
        for (;;) {
            counter++;
            char buf[32];
            snprintf(buf, sizeof(buf), "t%d", counter);
            if (!opt_str_in_list(reserved, r_count, buf)) {
                new_temps[i] = xstrdup(buf);
                break;
            }
        }
    }

    OptInstList out;
    opt_list_init(&out);
    for (size_t i = 0; i < body->count; ++i) {
        const IrInstruction *inst = &body->items[i];
        const char *new_dest = (inst->kind == IR_LABEL || inst->kind == IR_GOTO ||
                                inst->kind == IR_IF_FALSE || inst->kind == IR_PARAM ||
                                inst->kind == IR_LOCAL)
            ? inst->dest
            : opt_remap_tok(inst->dest, temps, new_temps, t_count);
        const char *new_a1 = opt_remap_tok(inst->arg1, temps, new_temps, t_count);
        const char *new_a2 = opt_remap_tok(inst->arg2, temps, new_temps, t_count);
        opt_list_push(&out, opt_clone_inst(inst->kind, inst->op, new_dest, new_a1, new_a2, inst->in_function));
    }

    opt_str_list_free(temps, t_count);
    opt_str_list_free(new_temps, t_count);
    opt_str_list_free(reserved, r_count);
    opt_list_free(body);
    *body = out;
}

static void opt_optimize_function_body(OptInstList *body, char **globals, size_t global_count) {
    opt_simplify_cfg(body);
    opt_simplify_algebraic(body);
    opt_fold_constants_and_branches(body);
    opt_hoist_licm(body, globals, global_count);
    opt_reduce_induction_vars(body);
    int cse_applied = opt_cse(body);
    opt_propagate_copies(body);
    opt_simplify_algebraic(body);
    opt_propagate_copies(body);
    opt_eliminate_dead_stores(body, globals, global_count);
    if (cse_applied) {
        opt_renumber_temps_if_needed(body);
    }
}

void ir_optimize(IrProgram *program) {
    if (!program || program->count == 0) return;

    char **globals = NULL;
    size_t global_count = 0, global_cap = 0;
    for (size_t i = 0; i < program->count; ++i) {
        if (program->items[i].kind == IR_GLOBAL && program->items[i].dest) {
            opt_str_list_add(&globals, &global_count, &global_cap, program->items[i].dest);
        }
    }

    OptInstList result;
    opt_list_init(&result);

    size_t idx = 0;
    while (idx < program->count) {
        const IrInstruction *inst = &program->items[idx];
        if (inst->kind == IR_FUNC_BEGIN) {
            opt_list_push(&result, opt_dup_inst(inst));
            idx++;
            OptInstList body;
            opt_list_init(&body);
            while (idx < program->count && program->items[idx].kind != IR_FUNC_END) {
                opt_list_push(&body, opt_dup_inst(&program->items[idx]));
                idx++;
            }
            opt_optimize_function_body(&body, globals, global_count);
            for (size_t k = 0; k < body.count; ++k) {
                opt_list_push(&result, opt_dup_inst(&body.items[k]));
            }
            opt_list_free(&body);
            if (idx < program->count && program->items[idx].kind == IR_FUNC_END) {
                opt_list_push(&result, opt_dup_inst(&program->items[idx]));
                idx++;
            }
        } else {
            opt_list_push(&result, opt_dup_inst(inst));
            idx++;
        }
    }

    opt_str_list_free(globals, global_count);
    ir_program_free(program);
    program->items = result.items;
    program->count = result.count;
    program->capacity = result.capacity;
}

