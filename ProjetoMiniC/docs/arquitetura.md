# Arquitetura do Compilador MiniC

O compilador **MiniC** possui implementações equivalentes em **Python** (`ProjetoMiniC/src/`) e **C** (`C/`), compartilhando o mesmo pipeline de etapas, contratos de linha de comando, códigos de saída e saídas textuais determinísticas.

## Visão Geral do Pipeline

```text
Código-Fonte (.c / .minic)
   │
   ▼
1. Analisador Léxico (Scanner)
   ├─ Python: ProjetoMiniC/src/lexer/scanner.py   | CLI: scanner.py
   └─ C:      C/scanner.c, C/token.c, C/errors.c  | CLI: scanner.c / C/minic_scanner
   │  (Saída: sequência de Tokens / JSONL; código de saída 2 se houver erro léxico)
   ▼
2. Analisador Sintático e AST (Parser)
   ├─ Python: ProjetoMiniC/src/parser/parser.py, ProjetoMiniC/src/ast/nodes.py | CLI: parser.py
   └─ C:      C/parser.c, C/ast.c                                              | CLI: parser.c / parser
   │  (Saída: Árvore Sintática Abstrata / S-expression; código de saída 3 se houver erro sintático)
   ▼
3. Analisador Semântico
   ├─ Python: ProjetoMiniC/src/semantic/analyzer.py | CLI: minic.py / main.py --semantic
   └─ C:      C/semantic.c                          | CLI: minic.c / minic
   │  (Saída: AST anotada com tipos, escopos, símbolos resolvidos e coerções; código de saída 4 se houver erro semântico)
   ▼
4. Gerador de Representação Intermediária (IR / TAC)
   ├─ Python: ProjetoMiniC/src/ir/ (instructions.py, generator.py, printer.py) | CLI: minic.py --ir / ir.py / main.py --ir
   └─ C:      C/ir.h, C/ir.c, C/ir_main.c                                      | CLI: minic --ir / ir.c / ir
   │  (Saída: Código de Três Endereços determinístico sem colisão de temporários/rótulos; código de saída 0)
   ▼
5. Otimizador de IR (-O1)
   ├─ Python: ProjetoMiniC/src/optimizer/optimizer.py                          | CLI: minic.py -O1 --ir / ir.py -O1
   └─ C:      C/optimizer.h, C/optimizer.c                                     | CLI: minic -O1 --ir / ir -O1
   │  (Passes: dobra/propagação de constantes, identidades algébricas, propagação de cópias,
   │   eliminação de código morto/inalcançável, CSE local, LICM e redução de força em laços)
   ▼
6. Gerador de Código (estrutura reservada para etapa futura)
   └─ Python: ProjetoMiniC/src/codegen/
```

## Contratos de Códigos de Saída

| Código | Significado |
|---:|---|
| `0` | Etapa concluída com sucesso |
| `1` | Uso incorreto da CLI ou erro de leitura de arquivo |
| `2` | Erro léxico detectado pelo Scanner |
| `3` | Erro sintático detectado pelo Parser |
| `4` | Erro semântico detectado pelo Analisador Semântico |
