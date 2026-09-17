# Projeto MiniC

Compilador para a linguagem **MiniC** (um subconjunto de C), desenvolvido em duas implementações paralelas:

- **Python** — implementação principal, em `ProjetoMiniC/src`
- **C** — implementação do analisador léxico, em `C/`

O objetivo é construir, em etapas, um pipeline de compilação completo: análise léxica, análise sintática, análise semântica, geração de código intermediário, otimização e geração de código final.

## Estado atual

| Etapa | Python | C |
|---|---|---|
| Análise léxica | ✅ Implementada | ✅ Implementada |
| Análise sintática | ✅ Parser descendente recursivo | ✅ Implementada |
| Análise semântica | 🚧 Estrutura criada (`src/semantic`), ainda não implementada | — |
| AST | ✅ Implementada | ✅ Implementada |
| Geração de código / IR / otimização | 🚧 Estruturas criadas (`src/codegen`, `src/ir`, `src/optimizer`) | — |

O lexer é o módulo mais maduro do projeto e serve de referência para os demais.

## Estrutura do repositório

```text
Projeto_MiniC/
├── main.py                      # Ponto de entrada raiz (CLI + GUI) da versão Python
├── scanner.py                   # Ponto de entrada alternativo, com resolução automática de path
├── Makefile                     # Build da versão em C (deve ser executado a partir de C/)
├── C/                            # Implementação do lexer em C
│   ├── main.c
│   ├── scanner.c / scanner.h
│   ├── token.c / token.h
│   ├── token_types.c / token_types.h
│   ├── errors.c / errors.h
│   └── util.c / util.h
└── ProjetoMiniC/                # Implementação em Python + recursos do projeto
    ├── docs/                     # Especificação, gramática (EBNF) e notas de arquitetura
    ├── casos-programas-c/        # Programas .c válidos usados como casos de teste
    ├── casos-invalidos/          # Casos .minic com erros léxicos propositais
    └── src/
        ├── lexer/                # Análise léxica (scanner, tokens, erros, JSONL, GUI)
        ├── parser/                # (em construção)
        ├── semantic/              # (em construção)
        ├── ast/                   # (em construção)
        ├── codegen/                # (em construção)
        ├── ir/                     # (em construção)
        └── optimizer/               # (em construção)
```

## Executando a versão em Python

Requer Python 3.10+ (o projeto usa `from __future__ import annotations`) e Tkinter instalado para a interface gráfica.

A partir da raiz do repositório:

```bash
python main.py
```

- Sem argumentos: abre o painel gráfico (Tkinter), com atalhos para cada etapa do compilador (as etapas ainda não implementadas exibem um aviso).
- Com um arquivo como argumento: roda a análise léxica em modo terminal.

```bash
python main.py caminho/para/arquivo.minic
python main.py caminho/para/arquivo.minic --tokens   # imprime só a tabela de tokens
python main.py caminho/para/arquivo.minic --errors   # imprime só os erros léxicos
python main.py caminho/para/arquivo.minic --jsonl    # imprime tokens/erros em JSONL
```

Alternativamente, é possível rodar o pacote do lexer diretamente, a partir da pasta `ProjetoMiniC`:

```bash
cd ProjetoMiniC
python -m src.lexer                                   # abre a interface gráfica do lexer
python -m src.lexer ../ProjetoMiniC/casos-invalidos/i01_simbolo_desconhecido.minic --jsonl
```

### Interface gráfica do lexer

A interface em Tkinter (`AplicacaoLexer`, em `src/lexer/__main__.py`) permite:

1. executar os testes embutidos do lexer (`demo.py`);
2. colar um trecho de código diretamente na interface e analisá-lo;
3. abrir um arquivo `.minic`, `.mc`, `.c` ou `.txt` e analisá-lo;
4. visualizar a saída formatada, os tokens em JSONL e os erros em JSONL em abas separadas, além de copiar o JSONL de tokens para a área de transferência.

## Executando a versão em C

A versão em C implementa o mesmo analisador léxico. O `Makefile`, na raiz do repositório, foi escrito para ser executado com o diretório de trabalho dentro de `C/`:

```bash
cd C
make -f ../Makefile          # compila o binário minic_scanner
./minic_scanner arquivo.c              # saída legível (tabela de tokens + diagnóstico)
./minic_scanner arquivo.c --jsonl      # saída apenas em JSONL (tokens no stdout, erros no stderr)
```

Alvos adicionais do Makefile (executados também a partir de `C/`):

```bash
make -f ../Makefile test-valid    # roda o scanner sobre os programas em casos-programas-c/
make -f ../Makefile test-invalid  # roda o scanner sobre os casos em casos-invalidos/
make -f ../Makefile test          # roda os dois conjuntos de teste
make -f ../Makefile clean         # remove binários e arquivos de saída gerados
```

## O que o lexer reconhece

- palavras reservadas, identificadores, números inteiros e reais, operadores e delimitadores;
- strings e caracteres, incluindo casos malformados;
- comentários de linha e de bloco;
- erros léxicos, como símbolos desconhecidos, comentários não terminados, strings/caracteres não terminados, números reais malformados e identificadores iniciados por dígito.

Cada token reconhecido carrega tipo, lexema, atributo (quando aplicável), linha e coluna. A saída pode ser formatada em tabela ou serializada em JSONL, seguindo o mesmo formato entre as versões Python e C.

## Casos de teste

- `ProjetoMiniC/casos-programas-c/`: programas `.c` válidos (Fibonacci, números primos, média de vetor, menu interativo, controle de temperatura), cada um com o `.expected.jsonl` correspondente.
- `ProjetoMiniC/casos-invalidos/`: trechos `.minic` com erros léxicos propositais, cada um com `.expected.jsonl` (tokens esperados) e `.errors.jsonl` (erros esperados).

## Documentação

- `ProjetoMiniC/docs/README.md`: detalhes específicos da implementação em Python.
- `ProjetoMiniC/docs/gramatica.ebnf`: gramática da linguagem MiniC.
- `ProjetoMiniC/docs/especificacao.md` e `docs/arquitetura.md`: ainda a serem preenchidos.

## Análise sintática — Etapa 2

O parser descendente recursivo consome diretamente os `Token` produzidos pelo
scanner e constrói uma AST tipada para declarações, funções, comandos e
expressões. O fluxo implementado é:

```text
Código fonte
    ↓
Scanner
    ↓
Tokens
    ↓
Parser descendente recursivo
    ↓
AST / Diagnóstico
```

A **AST** é a representação abstrata final usada pelo compilador. A aba
**Árvore Descendente** é uma visualização didática separada: ela registra as
regras realmente percorridas durante a análise, inclusive a cadeia de
precedência das expressões. Ela não substitui nem altera a AST.

```bash
# Python (somente biblioteca padrão)
python3 parser.py codigo.c

# C (compila o parser sem substituir o scanner da Etapa 1)
make parser
./parser codigo.c

# Regressão do parser (executa as mesmas entradas em Python e C)
make test-parser
```

Os 50 casos oficiais e suas saídas esperadas estão em
`testes-parser-50/testes-parser-50/casos`. Para executá-los:

```bash
python test_parser_50.py
python test_parser_50.py testes-parser-50/testes-parser-50/casos
python test_parser_50.py --detalhado
```

O runner compara exatamente a AST dos casos 01–25 e também confere o motivo do
diagnóstico nos casos 26–50. O modo detalhado mostra entrada, AST, diagnóstico,
tokens e Árvore Descendente de cada caso.

Na interface principal (`python3 main.py`), o botão **Análise Sintática** abre
uma tela própria para digitar ou carregar um arquivo, executar o parser e
consultar a AST, a Árvore Descendente, os diagnósticos com linha/coluna e os
tokens reconhecidos.

Os códigos de saída são: `0` para sucesso, `1` para uso/leitura inválidos,
`2` para erro léxico e `3` para erro sintático. A versão C usa apenas a
biblioteca padrão de C e a versão Python usa apenas a biblioteca padrão; o
`tkinter` é usado somente pelas interfaces gráficas dos analisadores léxico e
sintático.

Os testes de regressão cobrem declarações globais e locais (inclusive listas
separadas por vírgula), vetores, funções, parâmetros, controle de fluxo,
entrada/saída, chamadas, indexação, precedência e associatividade. Além de
aceitar ou rejeitar cada caso, eles verificam precedência, associatividade e o
contrato de execução das implementações.

## Tecnologias

- Python 3 + Tkinter (interface gráfica)
- C11 (gcc, make)
- JSONL como formato de intercâmbio de tokens/erros entre as implementações e os casos de teste
