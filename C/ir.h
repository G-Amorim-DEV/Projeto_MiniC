#ifndef IR_H
#define IR_H

#include "ast.h"
#include <stddef.h>
#include <stdio.h>

typedef enum {
    IR_GLOBAL,
    IR_FUNC_BEGIN,
    IR_FUNC_END,
    IR_PARAM,
    IR_LOCAL,
    IR_COPY,
    IR_UNARY,
    IR_BINARY,
    IR_ARRAY_LOAD,
    IR_ARRAY_STORE,
    IR_LABEL,
    IR_GOTO,
    IR_IF_FALSE,
    IR_ARG,
    IR_CALL,
    IR_RETURN,
    IR_PRINT,
    IR_READ
} IrOpKind;

typedef struct {
    IrOpKind kind;
    char *op;
    char *dest;
    char *arg1;
    char *arg2;
    int in_function;
} IrInstruction;

typedef struct {
    IrInstruction *items;
    size_t count;
    size_t capacity;
} IrProgram;

void ir_program_init(IrProgram *program);
void ir_program_free(IrProgram *program);
int ir_generate(const AstNode *ast_program, IrProgram *out_ir, FILE *err_stream);
char *ir_format(const IrProgram *program);
void ir_print(const IrProgram *program, FILE *out_stream);

#endif

