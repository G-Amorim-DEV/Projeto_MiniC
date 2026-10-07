#include "semantic.h"
#include "util.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

typedef enum { S_ERROR, S_INT, S_FLOAT, S_BOOL, S_CHAR, S_STRING, S_VOID } SemBase;
typedef struct { SemBase base; int array; } SemType;
typedef struct SemSymbol {
    char *name;
    SemType type;
    const char *category;
    int scope, line, column;
    AstNode *declaration;
    struct SemSymbol *next;
} SemSymbol;
typedef struct SemScope {
    int number;
    SemSymbol *symbols;
    struct SemScope *parent;
} SemScope;
typedef struct {
    int line, column, sequence;
    char *text;
} SemDiagnostic;
typedef struct {
    SemScope *scope;
    int next_scope, errors, loop_depth;
    AstNode *function;
    FILE *out;
    SemDiagnostic *diagnostics;
} SemContext;
enum { FLOW_NEXT=1, FLOW_RETURN=2, FLOW_BREAK=4, FLOW_CONTINUE=8 };
static SemType sem_type(SemBase base, int array) { SemType t={base,array}; return t; }
static SemType sem_named_type(const char *name) {
    SemBase base=S_ERROR;
    if(!strcmp(name,"int"))base=S_INT;
    else if(!strcmp(name,"float")||!strcmp(name,"real"))base=S_FLOAT;
    else if(!strcmp(name,"bool"))base=S_BOOL;
    else if(!strcmp(name,"char"))base=S_CHAR;
    else if(!strcmp(name,"string"))base=S_STRING;
    else if(!strcmp(name,"void"))base=S_VOID;
    return sem_type(base,0);
}
static const char *sem_type_text(SemType t) {
    static const char *scalar[]={"<error>","int","float","bool","char","string","void"};
    static const char *array[]={"<error>","int[]","float[]","bool[]","char[]","string[]","void[]"};
    return t.array?array[t.base]:scalar[t.base];
}
static int sem_numeric(SemType t) { return !t.array&&(t.base==S_INT||t.base==S_FLOAT); }
static int sem_compatible(SemType expected, SemType actual) {
    return expected.base==S_ERROR || actual.base==S_ERROR ||
        (expected.array==actual.array && (expected.base==actual.base ||
        (!expected.array&&expected.base==S_FLOAT&&actual.base==S_INT)));
}
static void sem_error(SemContext *c, const char *code, AstNode *n, const char *fmt, ...) {
    va_list args, copy;
    va_start(args,fmt); va_copy(copy,args);
    int size=vsnprintf(NULL,0,fmt,copy); va_end(copy);
    if(size<0){va_end(args);fputs("Erro ao formatar diagnóstico.\n",stderr);exit(1);}
    char *message=xmalloc((size_t)size+1);
    vsnprintf(message,(size_t)size+1,fmt,args);va_end(args);
    int prefix=snprintf(NULL,0,"%s — linha %d, coluna %d: ",code,n->line,n->column);
    char *text=xmalloc((size_t)prefix+(size_t)size+1);
    snprintf(text,(size_t)prefix+1,"%s — linha %d, coluna %d: ",code,n->line,n->column);
    memcpy(text+prefix,message,(size_t)size+1);free(message);
    c->diagnostics=xrealloc(c->diagnostics,(size_t)(c->errors+1)*sizeof(*c->diagnostics));
    SemDiagnostic *d=&c->diagnostics[c->errors];
    d->line=n->line;d->column=n->column;d->sequence=c->errors;d->text=text;c->errors++;
}
static int sem_diagnostic_order(const void *a,const void *b) {
    const SemDiagnostic *x=a,*y=b;
    if(x->line!=y->line)return x->line<y->line?-1:1;
    if(x->column!=y->column)return x->column<y->column?-1:1;
    return (x->sequence>y->sequence)-(x->sequence<y->sequence);
}
static void sem_push(SemContext *c) {
    SemScope *s=xmalloc(sizeof(*s));s->number=c->next_scope++;s->symbols=NULL;s->parent=c->scope;c->scope=s;
}
static void sem_pop(SemContext *c) {
    SemScope *s=c->scope; c->scope=s->parent;
    SemSymbol *symbol=s->symbols;
    while(symbol){SemSymbol *next=symbol->next;free(symbol->name);free(symbol);symbol=next;}
    free(s);
}
static SemSymbol *sem_lookup(SemContext *c, const char *name) {
    for(SemScope *s=c->scope;s;s=s->parent)
        for(SemSymbol *symbol=s->symbols;symbol;symbol=symbol->next)
            if(!strcmp(symbol->name,name))return symbol;
    return NULL;
}
/* Declaration labels are existing AST fields, not reparsed source syntax. */
static SemType sem_decl_type(AstNode *n) {
    const char *space=strchr(n->text,' ');
    size_t len=space?(size_t)(space-n->text):strlen(n->text);
    char *name=xmalloc(len+1);memcpy(name,n->text,len);name[len]=0;
    SemType t=sem_named_type(name);free(name);
    t.array=n->is_array || (n->kind==AST_VAR&&n->count&&n->children[0]);return t;
}
static char *sem_decl_name(AstNode *n) {
    const char *start=strchr(n->text,' '); start=start?start+1:n->text;
    const char *end=strchr(start,'(');size_t len=end?(size_t)(end-start):strlen(start);
    char *name=xmalloc(len+1);memcpy(name,start,len);name[len]=0;return name;
}
static void sem_declare(SemContext *c, AstNode *n, const char *category) {
    char *name=sem_decl_name(n);
    n->semantic_type=sem_type_text(sem_decl_type(n));
    n->semantic_scope=c->scope->number;n->semantic_category=category;
    n->array_dimension=n->kind==AST_VAR&&n->count?n->children[0]:NULL;
    for(SemSymbol *s=c->scope->symbols;s;s=s->next) {
        if(!strcmp(s->name,name)) {
            sem_error(c,"SEM002",n,"“%s” já declarado neste escopo; declaração anterior na linha %d, coluna %d (tipo %s).",name,s->line,s->column,sem_type_text(s->type));free(name);return;
        }
    }
    SemSymbol *s=xmalloc(sizeof(*s));s->name=name;s->type=sem_decl_type(n);s->category=category;
    s->scope=c->scope->number;s->line=n->line;s->column=n->column;s->declaration=n;
    s->next=c->scope->symbols;c->scope->symbols=s;
    n->resolved_declaration=n;
}
static void sem_expression_text(DynStr *out,AstNode *n) {
    if(n->source_text&&n->source_text[0]){dynstr_push_str(out,n->source_text);return;}
    if(n->kind==AST_ID){dynstr_push_str(out,n->text);return;}
    if(n->kind==AST_LIT){const char *comma=strchr(n->text,',');dynstr_push_str(out,comma?comma+1:n->text);return;}
    if(n->kind==AST_UNARY){dynstr_push_str(out,n->text);sem_expression_text(out,n->children[0]);return;}
    if(n->kind==AST_BINARY||n->kind==AST_ASSIGN){
        sem_expression_text(out,n->children[0]);dynstr_push_char(out,' ');
        dynstr_push_str(out,n->kind==AST_ASSIGN?"=":n->text);dynstr_push_char(out,' ');
        sem_expression_text(out,n->children[1]);return;
    }
    if(n->kind==AST_INDEX){sem_expression_text(out,n->children[0]);dynstr_push_char(out,'[');sem_expression_text(out,n->children[1]);dynstr_push_char(out,']');return;}
    if(n->kind==AST_CALL){sem_expression_text(out,n->children[0]);dynstr_push_char(out,'(');for(size_t i=1;i<n->count;i++){if(i>1)dynstr_push_str(out,", ");sem_expression_text(out,n->children[i]);}dynstr_push_char(out,')');}
}
static char *sem_text(AstNode *n) { DynStr text;dynstr_init(&text);sem_expression_text(&text,n);return text.data; }
static void sem_coercion(AstNode *n,SemType expected,SemType actual) {
    if(!expected.array&&!actual.array&&expected.base==S_FLOAT&&actual.base==S_INT){
        if(n->kind==AST_ASSIGN)n->chain_coercion_type="float";
        else n->coercion_type="float";
    }
}
static void sem_resolve(AstNode *n,SemSymbol *s) {
    n->resolved_declaration=s?s->declaration:NULL;
    if(s){
        n->semantic_category=s->category;n->semantic_scope=s->scope;
        n->array_dimension=s->declaration->array_dimension;
    }
}
static void sem_assignment_conversion(SemContext *c,AstNode *n,SemType expected,SemType actual,const char *target) {
    if(!sem_compatible(expected,actual)) {
        char *text=sem_text(n);
        sem_error(c,"SEM003",n,"Não é possível atribuir %s a %s sem conversão permitida (destino “%s”; expressão “%s”).",sem_type_text(actual),sem_type_text(expected),target,text);
        free(text);
    }else sem_coercion(n,expected,actual);
}
static void sem_conversion(SemContext *c,AstNode *n,SemType expected,SemType actual) {
    char *target=sem_text(n);sem_assignment_conversion(c,n,expected,actual,target);free(target);
}
static SemType sem_expression(SemContext *c,AstNode *n,int value);
static SemType sem_expression_for(SemContext *c,AstNode *n,int value,const char *context);
static void sem_assignable(SemContext *c,AstNode *n,SemType t) {
    if(t.base==S_ERROR)return;
    if((n->kind!=AST_ID&&n->kind!=AST_INDEX)||t.array){
        char *text=sem_text(n);
        if(n->kind==AST_LIT){
            const char *category="string";
            if(!strncmp(n->text,"int,",4))category="inteiro";
            else if(!strncmp(n->text,"real,",5))category="real";
            else if(!strncmp(n->text,"bool,",5))category="booleano";
            else if(!strncmp(n->text,"char,",5))category="caractere";
            sem_error(c,"SEM013",n,"Destino de atribuição não é atribuível; o literal %s “%s” não designa uma variável ou elemento de vetor.",category,text);
        }else sem_error(c,"SEM013",n,"Destino de atribuição não é atribuível; a expressão “%s” não designa uma variável ou elemento de vetor.",text);
        free(text);
    }
}
static void sem_condition(SemContext *c,AstNode *n,const char *kind) {
    SemType actual=sem_expression(c,n,1);
    if(actual.base!=S_ERROR&&(actual.base!=S_BOOL||actual.array)){
        char *text=sem_text(n);
        sem_error(c,"SEM005",n,"Condição de %s deve ter tipo bool; recebeu %s (expressão “%s”).",kind,sem_type_text(actual),text);free(text);
    }
}
static SemType sem_assignment(SemContext *c,AstNode *n) {
    int before=c->errors;
    SemType target=sem_expression(c,n->children[0],1);
    sem_assignable(c,n->children[0],target);
    SemType actual=n->children[1]->kind==AST_ASSIGN?sem_assignment(c,n->children[1]):sem_expression_for(c,n->children[1],1,"atribuição");
    char *target_text=sem_text(n->children[0]);
    sem_assignment_conversion(c,n->children[1],target,actual,target_text);free(target_text);
    int failed=c->errors>before||target.base==S_ERROR||actual.base==S_ERROR;
    n->semantic_type=failed?"<error>":"void";
    return failed?sem_type(S_ERROR,0):target;
}
static SemType sem_expression_inner(SemContext *c,AstNode *n) {
    if(n->kind==AST_LIT){const char *comma=strchr(n->text,',');size_t len=comma?(size_t)(comma-n->text):strlen(n->text);char *type=xmalloc(len+1);memcpy(type,n->text,len);type[len]=0;SemType t=sem_named_type(type);free(type);return t;}
    if(n->kind==AST_ID){
        SemSymbol *s=sem_lookup(c,n->text);
        sem_resolve(n,s);
        if(!s){sem_error(c,"SEM001",n,"Identificador “%s” não declarado neste escopo.",n->text);return sem_type(S_ERROR,0);}
        if(!strcmp(s->category,"function")){sem_error(c,"E_FUNCTION_VALUE",n,"A função '%s' deve ser chamada.",n->text);return sem_type(S_ERROR,0);}
        return s->type;
    }
    if(n->kind==AST_CALL){
        AstNode *callee=n->children[0];SemSymbol *s=callee->kind==AST_ID?sem_lookup(c,callee->text):NULL;
        sem_resolve(callee,s);sem_resolve(n,s);
        if(!s||strcmp(s->category,"function")){
            if(callee->kind==AST_ID&&!s){
                callee->semantic_type="<error>";
                sem_error(c,"SEM001",callee,"Identificador “%s” não declarado neste escopo.",callee->text);
            }else{
                int invalid=0;
                if(callee->kind==AST_ID)callee->semantic_type="<error>";
                else invalid=sem_expression(c,callee,1).base==S_ERROR;
                if(!invalid){char *text=sem_text(callee);sem_error(c,"E_CALL",callee,"'%s' não é uma função declarada.",text);free(text);}
            }
            for(size_t i=1;i<n->count;i++)sem_expression(c,n->children[i],1);
            return sem_type(S_ERROR,0);
        }
        callee->semantic_type="function";
        AstNode *fn=s->declaration;
        if(n->count-1!=fn->parameter_count)sem_error(c,"SEM007",n,"“%s” espera %zu argumentos, mas recebeu %zu.",s->name,fn->parameter_count,n->count-1);
        for(size_t i=1;i<n->count;i++) {
            SemType actual=sem_expression(c,n->children[i],1);
            if(i<=fn->parameter_count){
                SemType expected=sem_decl_type(fn->parameters[i-1]);
                if(!sem_compatible(expected,actual)){
                    char *text=sem_text(n->children[i]);
                    sem_error(c,"SEM008",n->children[i],"Argumento %zu de “%s”: esperado %s, recebido %s (expressão “%s”).",i,s->name,sem_type_text(expected),sem_type_text(actual),text);free(text);
                }else sem_coercion(n->children[i],expected,actual);
            }
        }
        return s->type;
    }
    if(n->kind==AST_INDEX){
        SemType target=sem_expression(c,n->children[0],1),index=sem_expression(c,n->children[1],1);
        if(index.base!=S_ERROR&&(index.base!=S_INT||index.array)){
            char *target_text=sem_text(n->children[0]),*index_text=sem_text(n->children[1]);
            sem_error(c,"SEM006",n->children[1],"Índice do vetor “%s” deve ser int; recebeu %s (expressão “%s”).",target_text,sem_type_text(index),index_text);free(target_text);free(index_text);
        }
        if(target.base==S_ERROR)return target;
        if(!target.array){char *text=sem_text(n->children[0]);sem_error(c,"E_ARRAY",n->children[0],"A expressão '%s' não é um vetor.",text);free(text);return sem_type(S_ERROR,0);}
        n->resolved_declaration=n->children[0]->resolved_declaration;
        n->semantic_category=n->children[0]->semantic_category;
        n->semantic_scope=n->children[0]->semantic_scope;
        n->array_dimension=n->children[0]->array_dimension;
        target.array=0;return target;
    }
    if(n->kind==AST_UNARY){
        SemType operand=sem_expression(c,n->children[0],1);if(operand.base==S_ERROR)return operand;
        int logical=!strcmp(n->text,"!");
        if((logical&&(operand.base!=S_BOOL||operand.array))||(!logical&&!sem_numeric(operand))){sem_error(c,"E_OPERATOR",n,"O operador '%s' exige operando %s.",n->text,logical?"bool":"numérico");return sem_type(S_ERROR,0);}
        return logical?sem_type(S_BOOL,0):operand;
    }
    if(n->kind==AST_BINARY){
        SemType left=sem_expression(c,n->children[0],1),right=sem_expression(c,n->children[1],1);
        if(left.base==S_ERROR||right.base==S_ERROR)return sem_type(S_ERROR,0);
        const char *op=n->text;int numeric=sem_numeric(left)&&sem_numeric(right),valid;
        int logical=!strcmp(op,"&&")||!strcmp(op,"||"),equality=!strcmp(op,"==")||!strcmp(op,"!=");
        int relation=!strcmp(op,"<")||!strcmp(op,"<=")||!strcmp(op,">")||!strcmp(op,">=");
        if(logical)valid=!left.array&&!right.array&&left.base==S_BOOL&&right.base==S_BOOL;
        else if(equality)valid=numeric||(!left.array&&!right.array&&left.base==right.base&&(left.base==S_BOOL||left.base==S_CHAR));
        else if(!strcmp(op,"%"))valid=!left.array&&!right.array&&left.base==S_INT&&right.base==S_INT;
        else valid=numeric;
        if(!valid){sem_error(c,"E_OPERATOR",n,"O operador '%s' não aceita os tipos '%s' e '%s'.",op,sem_type_text(left),sem_type_text(right));return sem_type(S_ERROR,0);}
        if(numeric&&(left.base==S_FLOAT||right.base==S_FLOAT)){
            sem_coercion(n->children[0],sem_type(S_FLOAT,0),left);
            sem_coercion(n->children[1],sem_type(S_FLOAT,0),right);
        }
        if(logical||equality||relation)return sem_type(S_BOOL,0);
        return sem_type(left.base==S_FLOAT||right.base==S_FLOAT?S_FLOAT:S_INT,0);
    }
    return sem_type(S_ERROR,0);
}
static SemType sem_expression_for(SemContext *c,AstNode *n,int value,const char *context) {
    int before=c->errors;
    SemType result=n->kind==AST_ASSIGN?sem_assignment(c,n):sem_expression_inner(c,n);
    if(result.base==S_ERROR||c->errors>before)result=sem_type(S_ERROR,0);
    else if(n->kind==AST_ASSIGN){
        result=sem_type(S_VOID,0);
        if(value){
            char *text=sem_text(n);
            sem_error(c,"SEM003",n,"A atribuição “%s” é um comando sem valor e não pode ser usada como expressão.",text);free(text);
            result=sem_type(S_ERROR,0);
        }
    }else if(result.base==S_VOID&&value){
        if(n->kind==AST_CALL&&n->children[0]->kind==AST_ID)
            sem_error(c,"SEM012",n,"Função “%s” não produz valor (retorno void) e não pode ser usada como expressão de %s.",n->children[0]->text,context);
        else {char *text=sem_text(n);sem_error(c,"SEM012",n,"A expressão “%s” de tipo void não pode ser usada como valor.",text);free(text);}
        result=sem_type(S_ERROR,0);
    }
    n->semantic_type=sem_type_text(result);
    return result;
}
static SemType sem_expression(SemContext *c,AstNode *n,int value) {
    return sem_expression_for(c,n,value,"valor");
}
static int sem_statement(SemContext *c,AstNode *n);
static int sem_block(SemContext *c,AstNode *n,int new_scope) {
    if(new_scope)sem_push(c);
    int flow=FLOW_NEXT;
    for(size_t i=0;i<n->count;i++){int result=sem_statement(c,n->children[i]);if(flow&FLOW_NEXT)flow=(flow&~FLOW_NEXT)|result;}
    if(new_scope)sem_pop(c);
    return flow;
}
static int sem_statement(SemContext *c,AstNode *n) {
    if(!n||n->kind==AST_NULL)return FLOW_NEXT;
    if(n->kind==AST_BLOCK)return sem_block(c,n,1);
    if(n->kind==AST_VAR){
        SemType t=sem_decl_type(n);sem_declare(c,n,t.array?"array":"variable");
        if(n->children[0])sem_conversion(c,n->children[0],sem_type(S_INT,0),sem_expression(c,n->children[0],1));
        if(n->children[1]){char *target=sem_decl_name(n);sem_assignment_conversion(c,n->children[1],t,sem_expression_for(c,n->children[1],1,"atribuição"),target);free(target);}
    }else if(n->kind==AST_EXPR_STMT){if(n->children[0]->kind!=AST_NULL)sem_expression(c,n->children[0],0);
    }else if(n->kind==AST_IF){
        sem_condition(c,n->children[0],"if");
        int a=sem_statement(c,n->children[1]);int b=sem_statement(c,n->children[2]);return a|b;
    }else if(n->kind==AST_WHILE||n->kind==AST_FOR){
        size_t cond=n->kind==AST_FOR?1:0,body=n->kind==AST_FOR?3:1;
        if(n->kind==AST_FOR&&n->children[0]->kind!=AST_NULL)sem_expression(c,n->children[0],0);
        if(n->children[cond]->kind!=AST_NULL)sem_condition(c,n->children[cond],n->kind==AST_FOR?"for":"while");
        if(n->kind==AST_FOR&&n->children[2]->kind!=AST_NULL)sem_expression(c,n->children[2],0);
        c->loop_depth++;int flow=sem_statement(c,n->children[body]);c->loop_depth--;return FLOW_NEXT|(flow&FLOW_RETURN);
    }else if(n->kind==AST_RETURN){
        AstNode *value=n->children[0];SemType actual=value->kind==AST_NULL?sem_type(S_VOID,0):sem_expression(c,value,1);
        if(!c->function)sem_error(c,"SEM010",n,"Retorno fora de uma função.");
        else {
            SemType expected=sem_decl_type(c->function);
            if(!sem_compatible(expected,actual)){
                char *name=sem_decl_name(c->function);
                sem_error(c,"SEM009",value->kind==AST_NULL?n:value,"Retorno %s incompatível com o tipo %s da função “%s”%s",sem_type_text(actual),sem_type_text(expected),name,
                    !actual.array&&!expected.array&&actual.base==S_FLOAT&&expected.base==S_INT?"; conversão implícita de float para int não permitida.":".");free(name);
            }else if(value->kind!=AST_NULL)sem_coercion(value,expected,actual);
        }
        return FLOW_RETURN;
    }else if(n->kind==AST_BREAK||n->kind==AST_CONTINUE){
        if(!c->loop_depth)sem_error(c,"SEM010",n,"%s só pode ocorrer dentro de laço.",n->kind==AST_BREAK?"break":"continue");
        return n->kind==AST_BREAK?FLOW_BREAK:FLOW_CONTINUE;
    }else if(n->kind==AST_PRINT)sem_expression(c,n->children[0],1);
    else if(n->kind==AST_READ)sem_assignable(c,n->children[0],sem_expression(c,n->children[0],1));
    return FLOW_NEXT;
}
static void sem_reset_annotations(AstNode *n) {
    if(!n)return;
    n->semantic_type=n->coercion_type=n->chain_coercion_type=n->semantic_category=NULL;
    n->semantic_scope=-1;n->resolved_declaration=n->array_dimension=NULL;
    for(size_t i=0;i<n->count;i++)sem_reset_annotations(n->children[i]);
    for(size_t i=0;i<n->parameter_count;i++)sem_reset_annotations(n->parameters[i]);
}
int semantic_analyze(AstNode *program,FILE *diagnostics) {
    sem_reset_annotations(program);
    SemContext c={NULL,0,0,0,NULL,diagnostics,NULL};sem_push(&c);
    for(size_t i=0;i<program->count;i++)if(program->children[i]->kind==AST_FUNCTION)sem_declare(&c,program->children[i],"function");
    for(size_t i=0;i<program->count;i++)if(program->children[i]->kind!=AST_FUNCTION)sem_statement(&c,program->children[i]);
    for(size_t i=0;i<program->count;i++){
        AstNode *n=program->children[i];if(n->kind!=AST_FUNCTION)continue;
        c.function=n;sem_push(&c);
        for(size_t j=0;j<n->parameter_count;j++)sem_declare(&c,n->parameters[j],"parameter");
        int flow=sem_block(&c,n->children[0],0);
        if(sem_decl_type(n).base!=S_VOID&&(flow&FLOW_NEXT)){
            char *name=sem_decl_name(n);
            AstNode origin=*n;origin.line=n->declaration_line;origin.column=n->declaration_column;
            AstNode *body=n->children[0],*last=body->count?body->children[body->count-1]:NULL;
            if(last&&last->kind==AST_IF&&last->children[2]->kind==AST_NULL){
                char *condition=sem_text(last->children[0]);
                sem_error(&c,"SEM011",&origin,"A função “%s” pode terminar sem retornar %s; o ramo em que “%s” é falso alcança o fim do corpo.",name,sem_type_text(sem_decl_type(n)),condition);free(condition);
            }else sem_error(&c,"SEM011",&origin,"A função “%s” pode terminar sem retornar %s; há um caminho que alcança o fim do corpo.",name,sem_type_text(sem_decl_type(n)));
            free(name);
        }
        sem_pop(&c);c.function=NULL;
    }
    sem_pop(&c);
    if(c.errors>1)qsort(c.diagnostics,(size_t)c.errors,sizeof(*c.diagnostics),sem_diagnostic_order);
    for(int i=0;i<c.errors;i++){fputs(c.diagnostics[i].text,c.out);fputs("\r\n",c.out);free(c.diagnostics[i].text);}
    free(c.diagnostics);return c.errors;
}
