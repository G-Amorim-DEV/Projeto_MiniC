#include "parser.h"
#include "scanner.h"
#include "semantic.h"
#include "util.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv) {
    if(argc!=2){fprintf(stderr,"Uso: ./minic <arquivo.c | arquivo.minic>\n");return 1;}
    char *source=read_file(argv[1]);
    if(!source){fprintf(stderr,"Erro ao ler arquivo '%s'.\n",argv[1]);return 1;}
    Scanner scanner;scanner_init(&scanner,source);scanner_scan_tokens(&scanner);
    if(scanner_has_errors(&scanner)){scanner_print_errors(&scanner);scanner_free(&scanner);free(source);return 2;}
    Parser parser;parser_init(&parser,scanner.tokens,scanner.tokens_len);parser.semantic_mode=1;
    AstNode *root=parser_parse(&parser);
    if(!root){scanner_free(&scanner);free(source);return 3;}
    int errors=semantic_analyze(root,stdout);
    if(errors)printf("Análise semântica concluída: %d %s; programa rejeitado.",errors,errors==1?"erro":"erros");
    else fputs("Análise semântica concluída: 0 erros; programa aceito.",stdout);
    ast_free(root);scanner_free(&scanner);free(source);return errors?4:0;
}
