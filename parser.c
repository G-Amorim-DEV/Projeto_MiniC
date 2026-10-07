#include "C/parser_main.c"
#include "C/parser.c"
#include "C/ast.c"
#define at_end scanner_at_end
#define peek scanner_peek
#define match scanner_match
#include "C/scanner.c"
#undef match
#undef peek
#undef at_end
#include "C/token.c"
#include "C/token_types.c"
#include "C/errors.c"
#include "C/util.c"
