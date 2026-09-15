# Especificação léxica do MiniC — Etapa 1

Esta é a especificação executável do scanner: os campos e os nomes externos
seguem os fixtures do projeto. A posição de cada token/erro é o início do seu
lexema, com linhas e colunas iniciando em 1.

## Regras reconhecidas

| Categoria | Regra |
| --- | --- |
| Identificador | `[A-Za-z_][A-Za-z0-9_]*` |
| Inteiro | `[0-9]+` |
| Real | `[0-9]+\.[0-9]+` |
| Caractere | `'c'` ou `'\\[nt\\'\"]'` |
| String | `"..."`, sem quebra de linha; escapes aceitos: `\n`, `\t`, `\\`, `\'`, `\"` |
| Espaços | espaço, tabulação, `\r` e `\n` |
| Comentários | `//` até a quebra de linha e `/* ... */` |

As palavras reservadas são `bool`, `int`, `float`, `char`, `void`, `true`,
`false`, `if`, `else`, `while`, `for`, `return`, `break`, `continue`, `print`
e `read`. Os operadores são `+ - * / % = == != < <= > >= && || !`; os
delimitadores são `( ) { } [ ] ; ,`. O ponto é preservado como `DOT` para
permitir a recuperação documentada de um real malformado (`12.`).

## Recuperação e erros

O scanner produz `UNKNOWN_SYMBOL`, `INVALID_IDENTIFIER`,
`MALFORMED_REAL_LITERAL`, `UNTERMINATED_STRING_LITERAL`,
`UNTERMINATED_BLOCK_COMMENT` e `UNTERMINATED_CHAR_LITERAL`. Para `123abc`,
emite o erro do lexema completo e, em seguida, os tokens `INT_LIT(123)` e
`IDENT(abc)`. Para `12.`, emite o erro e preserva `INT_LIT(12)` e `DOT`.

## Contrato de linha de comando

`python3 scanner.py arquivo.minic` e `C/minic_scanner arquivo.minic` escrevem
tokens em JSONL no stdout e erros em JSONL no stderr. Cada token contém
`token`, `lexeme`, `attribute`, `line` e `column`; cada erro contém `error`,
`lexeme`, `line` e `column`. A opção `--jsonl` é mantida por compatibilidade e
tem o mesmo comportamento padrão.
