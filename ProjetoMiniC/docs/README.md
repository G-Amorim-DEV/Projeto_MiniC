# MiniC em Python (`ProjetoMiniC`)

Este diretório contém a implementação modular do compilador **MiniC** em Python, cobrindo o pipeline completo desde a análise léxica até a geração e otimização de Representação Intermediária (IR / TAC), além de interfaces gráficas em Tkinter para cada etapa.

## Estrutura Principal

```text
ProjetoMiniC/src/
├── lexer/
│   ├── __init__.py
│   ├── __main__.py        # CLI e GUI (Tkinter) da Análise Léxica
│   ├── scanner.py         # Varredura léxica e emissão de tokens
│   ├── token_types.py     # Enumeração dos tipos de tokens e palavras reservadas
│   ├── tokens.py          # Estrutura de dados de Token e serialização JSONL
│   ├── errors.py          # Diagnósticos léxicos
│   └── demo.py            # Exemplos embutidos
├── parser/
│   ├── __init__.py
│   ├── __main__.py        # CLI e GUI (Tkinter) da Análise Sintática
│   └── parser.py          # Parser recursivo descendente
├── ast/
│   ├── __init__.py
│   └── nodes.py           # Nós da AST, formatação S-expression e árvore
├── semantic/
│   ├── __init__.py
│   ├── __main__.py        # CLI e GUI (Tkinter) da Análise Semântica
│   └── analyzer.py        # Analisador semântico (SEM001 a SEM013) e tabela de símbolos
├── ir/
│   ├── __init__.py
│   ├── __main__.py        # CLI e GUI (Tkinter) da Representação Intermediária
│   └── generator.py       # Gerador de Código de Três Endereços (TAC) sem colisão
├── optimizer/
│   ├── __init__.py
│   ├── __main__.py        # CLI e GUI (Tkinter) do Otimizador (-O0 vs -O1)
│   └── optimizer.py       # Passes de otimização de IR (-O1)
└── codegen/
    └── __init__.py        # Reservado para geração de código final
```

## Como Executar (a partir da raiz do repositório)

### Interfaces Gráficas (Tkinter)

```bash
python main.py                         # Painel principal (Launcher com todas as etapas)
python -m ProjetoMiniC.src.lexer       # GUI da Análise Léxica
python -m ProjetoMiniC.src.parser      # GUI da Análise Sintática (AST)
python -m ProjetoMiniC.src.semantic    # GUI da Análise Semântica
python -m ProjetoMiniC.src.ir          # GUI da Representação Intermediária (TAC)
python -m ProjetoMiniC.src.optimizer   # GUI do Otimizador de IR (-O0 vs -O1)
```

### Linha de Comando (CLI)

```bash
python scanner.py arquivo.c --jsonl    # Etapa 1: Tokens e erros em JSONL
python parser.py arquivo.c             # Etapa 2: AST em S-expression
python minic.py arquivo.c              # Etapa 3: Análise Semântica
python minic.py --ir arquivo.c         # Etapa 4: Geração de IR (TAC -O0)
python minic.py --ir -O1 arquivo.c     # Etapa 5: Geração de IR Otimizada (-O1)
python ir.py arquivo.c                 # Atalho direto para IR (-O0)
python ir.py -O1 arquivo.c             # Atalho direto para IR (-O1)
```
