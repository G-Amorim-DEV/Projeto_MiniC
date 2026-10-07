/*
 * Entry point expected by test_scanner_c.sh.
 *
 * The scanner implementation is deliberately split into modules under C/.
 * This translation unit amalgamates those modules so the official command
 * `gcc scanner.c -o scanner` builds the complete CLI without requiring the
 * test harness to know the project's internal directory layout.
 */
#include "C/util.c"
#include "C/token_types.c"
#include "C/errors.c"
#include "C/token.c"
#include "C/scanner.c"
#include "C/main.c"
