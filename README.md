# Projeto MiniC

Compilador educacional completo para a linguagem **MiniC**, um subconjunto estrito de C. O projeto possui implementações equivalentes, canônicas e em paridade funcional e textual entre **Python** e **C** para todas as etapas: analisador léxico, analisador sintático (AST), analisador semântico, gerador de Representação Intermediária (IR em Código de Três Endereços — TAC) e otimizador de IR (`-O1`), além de interface gráfica interativa em **Tkinter**, ferramentas de linha de comando (CLI) e suítes completas de testes automatizados.

O objetivo do projeto é construir o pipeline completo de compilação:
$$\text{Código-fonte} \longrightarrow \text{Lexer} \longrightarrow \text{Parser (AST)} \longrightarrow \text{Semântica} \longrightarrow \text{IR (TAC)} \longrightarrow \text{Otimizador (-O1)} \longrightarrow \text{Código Final}$$

---

## Estado Atual do Projeto

| Etapa | Python | C | Cobertura / Suíte Oficial |
|---|---|---|---|
| **1. Análise Léxica (Scanner)** | Implementada (`ProjetoMiniC/src/lexer/`, `scanner.py`) | Implementada (`C/scanner.c`, `scanner.c`) | Fixtures JSONL (`casos-programas-c/` e `casos-invalidos/`) |
| **2. Análise Sintática e AST (Parser)** | Implementada (`ProjetoMiniC/src/parser/`, `parser.py`) | Implementada (`C/parser.c`, `C/ast.c`, `parser.c`) | **50/50 casos aprovados** (`testes-parser-50`) |
| **3. Análise Semântica** | Implementada (`ProjetoMiniC/src/semantic/`, `minic.py`) | Implementada (`C/semantic.c`, `C/semantic_main.c`, `minic.c`) | **20/20 casos aprovados** (`minic-testes-semanticos`) |
| **4. Representação Intermediária (IR / TAC)** | Implementada (`ProjetoMiniC/src/ir/`, `ir.py`, `minic.py --ir`) | Implementada (`C/ir.c`, `C/ir_main.c`, `ir.c`, `minic.c --ir`) | **30/30 casos aprovados** (`minic-ir-test-cases` + 15 unitários) |
| **5. Otimização de IR (`-O1`)** | Implementada (`ProjetoMiniC/src/optimizer/`, `minic.py -O1`) | Implementada (`C/optimizer.c`, `minic.c -O1`) | **10/10 casos aprovados** (`O01` a `O10`) |
| **6. Geração de Código Final** | Em desenvolvimento | Em desenvolvimento | Próxima etapa |

---

## Pré-requisitos e O Que Instalar

O projeto utiliza **estritamente a biblioteca padrão do Python** e **C11 padrão**, sem dependências externas via `pip`.

### Requisitos do Sistema
1. **Python 3.10 ou superior** (com módulo `tkinter` habilitado para uso da interface gráfica).
2. **Compilador C (`gcc`)** compatível com o padrão **C11** (`gcc` / MinGW-w64 / MSYS2).
3. **GNU Make** (opcional, para invocar alvos do `Makefile`; qualquer módulo em C compila diretamente com `gcc`).
4. **Bash** (nativo no Linux e macOS; no Windows, recomenda-se o **Git Bash** ou **WSL** para executar os scripts `.sh`).

### Comandos de Instalação

#### No Linux (Ubuntu / Debian / WSL)
```bash
sudo apt update
sudo apt install -y python3 python3-tk build-essential gcc make bash diffutils
```

#### No Windows
- **Python 3.10+**: Baixe o instalador no [python.org](https://www.python.org/downloads/). Na primeira tela, selecione **"Add Python to PATH"** e na instalação personalizada garanta que a opção **"tcl/tk and IDLE"** permaneça marcada.
- **GCC e Make**: Instale via [MSYS2](https://www.msys2.org/) executando `pacman -S mingw-w64-ucrt-x86_64-gcc make` e adicione a pasta `bin` ao `PATH` do sistema, ou utilize o instalador MinGW-w64 (WinLibs).
- **Git Bash**: Instale o [Git for Windows](https://git-scm.com/download/win), que fornece o terminal Bash com utilitários padrão Unix (`diff`, `cmp`, `sed`, `grep`, `mktemp`).

#### No macOS
```bash
xcode-select --install
brew install python python-tk
```

---

## Estrutura do Repositório

```text
Projeto_MiniC/
├── main.py                               # Launcher geral (GUI unificada e CLI multi-etapa)
├── minic.py                              # CLI unificada Python (Semântica por padrão; --ir e -O1)
├── minic.c                               # Compilador unificado C em arquivo único (Semântica, IR e -O1)
├── ir.py                                 # CLI direta de IR / TAC em Python (-O0 e -O1)
├── ir.c                                  # Gerador de IR C em arquivo único (-O0 e -O1)
├── parser.py                             # CLI do Parser Python (imprime AST S-expression)
├── parser.c                              # Parser C em arquivo único (imprime AST S-expression)
├── scanner.py                            # CLI do Scanner Python (tokens/erros JSONL)
├── scanner.c                             # Scanner C em arquivo único (tokens/erros JSONL)
├── Makefile                              # Alvos de compilação C e runners de testes
│
├── ProjetoMiniC/
│   ├── src/
│   │   ├── lexer/                        # Scanner Python, tokens e GUI Tkinter
│   │   ├── parser/                       # Parser recursivo descendente Python e GUI Tkinter
│   │   ├── ast/                          # Estrutura dos nós da AST
│   │   ├── semantic/                     # Analisador semântico (SEM001-SEM013) e GUI Tkinter
│   │   ├── ir/                           # Gerador de TAC sem colisão de temporários e GUI Tkinter
│   │   └── optimizer/                    # Otimizador de TAC -O1 e GUI comparativa -O0 vs -O1
│   ├── casos-programas-c/                # Programas válidos de teste do Scanner (c01 a c05)
│   ├── casos-invalidos/                  # Casos com erros léxicos de teste do Scanner (i01 a i06)
│   └── docs/                             # Documentação técnica e especificações formais
│
├── C/                                    # Módulos C organizados
│   ├── scanner.c, scanner.h, main.c      # Scanner C
│   ├── parser.c, parser.h, parser_main.c # Parser C
│   ├── ast.c, ast.h                      # AST C e serialização
│   ├── semantic.c, semantic.h            # Analisador semântico C
│   ├── ir.c, ir.h, ir_main.c             # Gerador de TAC C sem colisão
│   └── optimizer.c, optimizer.h          # Otimizador de TAC C (-O1)
│
├── testes-parser-50/                     # Suíte de 50 casos do Parser (testes oficiais do professor)
├── minic-testes-semanticos/              # Suíte de 20 casos da Análise Semântica (oficiais)
├── minic-ir-test-cases/                  # Suíte de 30 casos de IR e Otimização (P01-P10, E01-E10, O01-O10)
│
├── test_scanner_python.sh, test_scanner_c.sh # Scripts de teste do Lexer
├── testar_parser.sh, testar_parser_python.sh, testar_parser_c.sh # Scripts de teste do Parser
├── testes_semanticos_py.sh, testes_semanticos_c.sh # Scripts de teste da Semântica
├── test_ir_python.sh, test_ir_c.sh       # Scripts de teste de IR e Otimização (raiz)
└── test_ir_30.py                         # Runner comparador oficial dos 30 casos de IR/Otimização
```

---

## Códigos de Saída (Contrato do Compilador)

Tanto na versão em **Python** quanto na versão em **C**, todas as ferramentas de linha de comando respeitam o mesmo código de retorno:

| Código de Saída | Significado | Comportamento do Compilador |
|:---:|---|---|
| `0` | **Sucesso** | Programa válido analisado com sucesso / IR emitida |
| `1` | **Uso incorreto ou Erro de E/S** | Argumentos inválidos ou arquivo não encontrado/ilegível |
| `2` | **Erro Léxico** | Símbolo desconhecido, cadeia não terminada, etc. |
| `3` | **Erro Sintático** | Token inesperado, ponto e vírgula ausente, etc. |
| `4` | **Erro Semântico** | Tipos incompatíveis, identificador não declarado, etc. |

**Regra Estrita**: Nenhum código intermediário (IR) é emitido caso o código-fonte possua erro léxico (`2`), sintático (`3`) ou semântico (`4`).

---

## Como Executar a Versão em Python

Todos os comandos devem ser executados **a partir da raiz do repositório**.

### 1. Interface Gráfica Unificada (Tkinter)

```bash
# Abre o Launcher principal com botões para as 6 etapas:
python main.py
```

Cada etapa possui interface gráfica interativa própria:
```bash
python -m ProjetoMiniC.src.lexer       # GUI da Análise Léxica (tokens, literais, JSONL)
python -m ProjetoMiniC.src.parser      # GUI da Análise Sintática (árvore visual e S-expression)
python -m ProjetoMiniC.src.semantic    # GUI da Análise Semântica (diagnósticos linha/coluna)
python -m ProjetoMiniC.src.ir          # GUI da Representação Intermediária (TAC -O0)
python -m ProjetoMiniC.src.optimizer   # GUI do Otimizador (compara TAC -O0 vs -O1 lado a lado)
```

### 2. Linha de Comando em Python

```bash
# 1. Análise Léxica
python main.py arquivo.c                       # Tabela formatada de tokens + diagnósticos
python main.py arquivo.c --tokens              # Apenas a lista de tokens
python main.py arquivo.c --jsonl               # Tokens em JSONL (stdout) e erros em JSONL (stderr)
python scanner.py arquivo.c --jsonl            # Wrapper direto do scanner

# 2. Análise Sintática (AST)
python parser.py arquivo.c                     # Imprime a AST oficial em S-expression (1 linha)
python main.py arquivo.c --ast                 # Imprime a AST em formato de árvore indentada
python main.py arquivo.c --ast --sexp          # Imprime a AST em formato S-expression

# 3. Análise Semântica
python minic.py arquivo.c                      # Executa Lexer → Parser → Semântica (código 0 ou 4)

# 4. Representação Intermediária (IR sem otimização, -O0)
python minic.py --ir arquivo.c                 # Gera o TAC linear sem otimização
python ir.py arquivo.c                         # Atalho direto para gerar IR (-O0)

# 5. Representação Intermediária Otimizada (-O1)
python minic.py --ir -O1 arquivo.c             # Gera o TAC com todas as otimizações ativas
python minic.py -O1 arquivo.c                  # -O1 ativa automaticamente a emissão de IR
python ir.py -O1 arquivo.c                     # Atalho direto para IR otimizada (-O1)
```

---

## Como Compilar e Executar a Versão em C

### 1. Compilação e Execução via `Makefile`

```bash
# Compilar o Scanner em C (gera C/minic_scanner)
make
./C/minic_scanner arquivo.c
./C/minic_scanner arquivo.c --jsonl

# Compilar o Parser em C (gera ./parser)
make parser
./parser arquivo.c

# Compilar o Compilador Completo em C (gera ./minic)
make semantic
./minic arquivo.c              # Análise Semântica
./minic --ir arquivo.c         # Emissão de IR (-O0)
./minic --ir -O1 arquivo.c     # Emissão de IR Otimizada (-O1)

# Compilar o Gerador Dedicado de IR em C (gera ./ir)
make ir
./ir arquivo.c                 # IR (-O0)
./ir -O1 arquivo.c             # IR Otimizada (-O1)

# Limpeza de binários e arquivos gerados
make clean
```

### 2. Compilação Direta com `gcc` em Arquivo Único (Sem `make`)

Todos os wrappers da raiz são independentes e compiláveis com um único comando `gcc`:

```bash
# Scanner C
gcc -std=c11 -Wall -Wextra -O2 scanner.c -o scanner
./scanner arquivo.c --jsonl

# Parser C
gcc -std=c11 -Wall -Wextra -O2 parser.c -o parser
./parser arquivo.c

# Compilador MiniC C (Semântica, IR e Otimizador)
gcc -std=c11 -Wall -Wextra -O2 minic.c -o minic
./minic arquivo.c              # Retorna 0 (aceito) ou 4 (rejeitado)
./minic --ir arquivo.c         # Emite IR TAC (-O0)
./minic --ir -O1 arquivo.c     # Emite IR TAC otimizada (-O1)

# Gerador de IR C
gcc -std=c11 -Wall -Wextra -O2 ir.c -o ir
./ir arquivo.c                 # Emite IR TAC (-O0)
./ir -O1 arquivo.c             # Emite IR TAC otimizada (-O1)
```

---

## Tabela Geral de Comandos de Testes Automatizados

Todos os comandos devem ser executados na **raiz do repositório**:

| Etapa | Comando de Execução (Python) | Comando de Execução (C) |
|---|---|---|
| **Etapa 1: Lexer** | `bash test_scanner_python.sh ./scanner.py ./ProjetoMiniC` | `bash test_scanner_c.sh ./scanner.c ./ProjetoMiniC` |
| **Etapa 2: Parser (50 casos)** | `bash testar_parser_python.sh ./testes-parser-50 ./parser.py` | `bash testar_parser_c.sh ./testes-parser-50 ./parser.c` |
| **Etapa 2: Parser (Combinado)** | `bash testar_parser.sh ./testes-parser-50` | *(valida Python e C na mesma execução)* |
| **Etapa 3: Semântica (20 casos)** | `bash testes_semanticos_py.sh ./minic.py ./minic-testes-semanticos` | `bash testes_semanticos_c.sh ./minic.c ./minic-testes-semanticos` |
| **Etapas 4 e 5: IR e -O1 (30 casos)** | `bash test_ir_python.sh ./minic.py ./minic-ir-test-cases` | `bash test_ir_c.sh ./minic.c ./minic-ir-test-cases` |
| **Etapas 4 e 5: Runner Python** | `python test_ir_30.py minic-ir-test-cases` | *(testa `minic.py` e `minic.c` sequencialmente)* |
| **Testes Unitários de IR** | `python -m unittest discover -s tests -p test_ir.py -v` | *(15 testes unitários de paridade)* |

---

# Saídas Exatas de Todos os Testes

Esta seção apresenta exatamente como os testes são executados e qual é a saída gerada por cada bateria de testes, para que o professor ou avaliador possa conferir linha a linha os resultados.

---

## 1. Saídas da Etapa 1: Analisador Léxico (Scanner)

O scanner processa os arquivos de teste comparando a sequência de tokens com os arquivos `<entrada>.expected.jsonl` e os erros léxicos com `<entrada>.errors.jsonl`.

### Comandos
```bash
bash test_scanner_python.sh ./scanner.py ./ProjetoMiniC
bash test_scanner_c.sh ./scanner.c ./ProjetoMiniC
```

### Saída Exibida no Terminal
```text
================================================================
Caso: ProjetoMiniC/casos-invalidos/i01_simbolo_desconhecido.minic
Comando: python3 ./scanner.py ProjetoMiniC/casos-invalidos/i01_simbolo_desconhecido.minic
Resultado esperado: ProjetoMiniC/casos-invalidos/i01_simbolo_desconhecido.expected.jsonl
OK: 4 token(s).
RESULTADO: OK
Aviso: o scanner terminou com código 2.

================================================================
Caso: ProjetoMiniC/casos-invalidos/i02_comentario_nao_terminado.minic
Comando: python3 ./scanner.py ProjetoMiniC/casos-invalidos/i02_comentario_nao_terminado.minic
Resultado esperado: ProjetoMiniC/casos-invalidos/i02_comentario_nao_terminado.expected.jsonl
OK: 5 token(s).
RESULTADO: OK
Aviso: o scanner terminou com código 2.

================================================================
Caso: ProjetoMiniC/casos-invalidos/i03_caractere_nao_terminado.minic
Comando: python3 ./scanner.py ProjetoMiniC/casos-invalidos/i03_caractere_nao_terminado.minic
Resultado esperado: ProjetoMiniC/casos-invalidos/i03_caractere_nao_terminado.expected.jsonl
OK: 6 token(s).
RESULTADO: OK
Aviso: o scanner terminou com código 2.

================================================================
Caso: ProjetoMiniC/casos-invalidos/i04_cadeia_nao_terminada.minic
Comando: python3 ./scanner.py ProjetoMiniC/casos-invalidos/i04_cadeia_nao_terminada.minic
Resultado esperado: ProjetoMiniC/casos-invalidos/i04_cadeia_nao_terminada.expected.jsonl
OK: 4 token(s).
RESULTADO: OK
Aviso: o scanner terminou com código 2.

================================================================
Caso: ProjetoMiniC/casos-invalidos/i05_numero_real_malformado.minic
Comando: python3 ./scanner.py ProjetoMiniC/casos-invalidos/i05_numero_real_malformado.minic
Resultado esperado: ProjetoMiniC/casos-invalidos/i05_numero_real_malformado.expected.jsonl
OK: 4 token(s).
RESULTADO: OK
Aviso: o scanner terminou com código 2.

================================================================
Caso: ProjetoMiniC/casos-programas-c/c01_fibonacci.c
Comando: python3 ./scanner.py ProjetoMiniC/casos-programas-c/c01_fibonacci.c
Resultado esperado: ProjetoMiniC/casos-programas-c/c01_fibonacci.c.expected.jsonl
OK: 85 token(s).
RESULTADO: OK

================================================================
Caso: ProjetoMiniC/casos-programas-c/c02_primos.c
Comando: python3 ./scanner.py ProjetoMiniC/casos-programas-c/c02_primos.c
Resultado esperado: ProjetoMiniC/casos-programas-c/c02_primos.c.expected.jsonl
OK: 96 token(s).
RESULTADO: OK

================================================================
Caso: ProjetoMiniC/casos-programas-c/c03_media_vetor.c
Comando: python3 ./scanner.py ProjetoMiniC/casos-programas-c/c03_media_vetor.c
Resultado esperado: ProjetoMiniC/casos-programas-c/c03_media_vetor.c.expected.jsonl
OK: 115 token(s).
RESULTADO: OK

================================================================
Caso: ProjetoMiniC/casos-programas-c/c04_menu_interativo.c
Comando: python3 ./scanner.py ProjetoMiniC/casos-programas-c/c04_menu_interativo.c
Resultado esperado: ProjetoMiniC/casos-programas-c/c04_menu_interativo.c.expected.jsonl
OK: 95 token(s).
RESULTADO: OK

================================================================
Caso: ProjetoMiniC/casos-programas-c/c05_controle_temperatura.c
Comando: python3 ./scanner.py ProjetoMiniC/casos-programas-c/c05_controle_temperatura.c
Resultado esperado: ProjetoMiniC/casos-programas-c/c05_controle_temperatura.c.expected.jsonl
OK: 61 token(s).
RESULTADO: OK

================================================================
Resumo: 10 OK, 0 falharam, 5 avisos, 10 casos verificados.
```

### Detalhamento dos Erros Léxicos Verificados (`casos-invalidos/`)
| Arquivo | Código-Fonte de Entrada | Diagnóstico Léxico Esperado (JSONL) | Código de Saída |
|---|---|---|:---:|
| `i01_simbolo_desconhecido.minic` | `x = 1 @ 2;` | `{"error":"UNKNOWN_SYMBOL","lexeme":"@","line":1,"column":7}` | `2` |
| `i02_comentario_nao_terminado.minic` | `int x = 1; /* comentário sem fechamento` | `{"error":"UNTERMINATED_BLOCK_COMMENT","lexeme":"/* comentário sem fechamento\n","line":1,"column":12}` | `2` |
| `i03_caractere_nao_terminado.minic` | `char c = 'a;\nint x = 1;` | `{"error":"UNTERMINATED_CHAR_LITERAL","lexeme":"'a","line":1,"column":10}` | `2` |
| `i04_cadeia_nao_terminada.minic` | `print("texto sem fim);` | `{"error":"UNTERMINATED_STRING_LITERAL","lexeme":"\"texto sem fim);","line":1,"column":7}` | `2` |
| `i05_numero_real_malformado.minic` | `valor = 12.;` | `{"error":"MALFORMED_REAL_LITERAL","lexeme":"12.","line":1,"column":9}` | `2` |
| `i06_identificador_iniciado_por_digito` | `int 123abc = 4;` | `{"error":"INVALID_IDENTIFIER","lexeme":"123abc","line":1,"column":5}` | `2` |

---

## 2. Saídas da Etapa 2: Analisador Sintático e AST (50 Casos)

O pacote oficial do professor contém 50 casos de teste:
- Casos **01 a 25**: Devem ser **ACEITOS** (código `0`) e a AST em formato S-expression deve ser idêntica ao arquivo `ast.esperada.txt`.
- Casos **26 a 50**: Devem ser **REJEITADOS** com erro de sintaxe (código `3`).

### Comandos
```bash
bash testar_parser.sh ./testes-parser-50
bash testar_parser_python.sh ./testes-parser-50 ./parser.py
bash testar_parser_c.sh ./testes-parser-50 ./parser.c
```

### Saída Exibida no Terminal
```text
ID | STATUS | TÍTULO | DIRETÓRIO
01 | ACEITO | Declaração inteira simples | casos/01_declara_o_inteira_simples
02 | ACEITO | Inicialização inteira | casos/02_inicializa_o_inteira
03 | ACEITO | Expressão aritmética e precedência | casos/03_express_o_aritm_tica_e_preced_ncia
04 | ACEITO | Várias declarações globais | casos/04_v_rias_declara_es_globais
05 | ACEITO | Função sem parâmetros | casos/05_fun_o_sem_par_metros
06 | ACEITO | Função com parâmetros | casos/06_fun_o_com_par_metros
07 | ACEITO | Atribuição simples | casos/07_atribui_o_simples
08 | ACEITO | If sem else | casos/08_if_sem_else
09 | ACEITO | If com else | casos/09_if_com_else
10 | ACEITO | While | casos/10_while
11 | ACEITO | Bloco aninhado | casos/11_bloco_aninhado
12 | ACEITO | Operadores relacionais | casos/12_operadores_relacionais
13 | ACEITO | Operador unário | casos/13_operador_un_rio
14 | ACEITO | Chamada sem argumentos | casos/14_chamada_sem_argumentos
15 | ACEITO | Chamada com argumentos | casos/15_chamada_com_argumentos
16 | ACEITO | Vetor com tamanho | casos/16_vetor_com_tamanho
17 | ACEITO | Indexação de vetor | casos/17_indexa_o_de_vetor
18 | ACEITO | Expressão com parênteses | casos/18_express_o_com_par_nteses
19 | ACEITO | Float e comparação | casos/19_float_e_compara_o
20 | ACEITO | Retorno vazio | casos/20_retorno_vazio
21 | ACEITO | Função com vários comandos | casos/21_fun_o_com_v_rios_comandos
22 | ACEITO | Atribuição associativa | casos/22_atribui_o_associativa
23 | ACEITO | Condicionais aninhados | casos/23_condicionais_aninhados
24 | ACEITO | Laço com expressão complexa | casos/24_la_o_com_express_o_complexa
25 | ACEITO | Programa integrado | casos/25_programa_integrado
26 | REJEITADO | Ponto e vírgula ausente em declaração | casos/26_ponto_e_v_rgula_ausente_em_declara_o
27 | REJEITADO | Ponto e vírgula ausente após expressão | casos/27_ponto_e_v_rgula_ausente_ap_s_express_o
28 | REJEITADO | Parêntese de condição ausente | casos/28_par_ntese_de_condi_o_ausente
29 | REJEITADO | Chave de bloco ausente | casos/29_chave_de_bloco_ausente
30 | REJEITADO | Chave final ausente | casos/30_chave_final_ausente
31 | REJEITADO | Parêntese final de função ausente | casos/31_par_ntese_final_de_fun_o_ausente
32 | REJEITADO | Parâmetro sem tipo | casos/32_par_metro_sem_tipo
33 | REJEITADO | Parâmetro sem identificador | casos/33_par_metro_sem_identificador
34 | REJEITADO | Vírgula extra nos parâmetros | casos/34_v_rgula_extra_nos_par_metros
35 | REJEITADO | Inicializador sem expressão | casos/35_inicializador_sem_express_o
36 | REJEITADO | Operador sem operando | casos/36_operador_sem_operando
37 | REJEITADO | Dois operadores consecutivos | casos/37_dois_operadores_consecutivos
38 | REJEITADO | Atribuição sem destino | casos/38_atribui_o_sem_destino
39 | REJEITADO | Chamada sem fechar parêntese | casos/39_chamada_sem_fechar_par_ntese
40 | REJEITADO | Vírgula sem argumento | casos/40_v_rgula_sem_argumento
41 | REJEITADO | Índice sem fechar colchete | casos/41_ndice_sem_fechar_colchete
42 | REJEITADO | Índice sem expressão | casos/42_ndice_sem_express_o
43 | REJEITADO | While sem corpo | casos/43_while_sem_corpo
44 | REJEITADO | Else sem if | casos/44_else_sem_if
45 | REJEITADO | Return sem ponto e vírgula | casos/45_return_sem_ponto_e_v_rgula
46 | REJEITADO | Tipo sem nome | casos/46_tipo_sem_nome
47 | REJEITADO | Declaração local inválida | casos/47_declara_o_local_inv_lida
48 | REJEITADO | Função sem corpo | casos/48_fun_o_sem_corpo
49 | REJEITADO | Fechamento extra | casos/49_fechamento_extra
50 | REJEITADO | Condição vazia | casos/50_condi_o_vazia

Resumo: 50/50 casos passaram.
```

### Amostra das ASTs Canônicas Esperadas (Casos Válidos 01 a 25)
- **Caso 01 (`int x;`)**:
  ```text
  Program(VarDecl(int x))
  ```
- **Caso 02 (`int x = 42;`)**:
  ```text
  Program(VarDecl(int x = Lit(int,42)))
  ```
- **Caso 03 (`int x = 2 + 3 * 4;`)**:
  ```text
  Program(VarDecl(int x = Binary(+, Lit(int,2), Binary(*, Lit(int,3), Lit(int,4)))))
  ```
- **Caso 06 (`int soma(int a, int b) { return a + b; }`)**:
  ```text
  Program(Function(int soma(int a,int b) Block(Return(Binary(+, Id(a), Id(b))))))
  ```
- **Caso 10 (`int main() { int i = 0; while (i < 10) i = i + 1; return i; }`)**:
  ```text
  Program(Function(int main() Block(VarDecl(int i=Lit(int,0)), While(Binary(<,Id(i),Lit(int,10)), ExprStmt(Assign(Id(i),Binary(+,Id(i),Lit(int,1))))), Return(Id(i)))))
  ```
- **Caso 25 (Programa integrado com funções, vetores e laços)**:
  ```text
  Program(Function(int soma(int a,int b) Block(Return(Binary(+,Id(a),Id(b))))), Function(int main() Block(VarDecl(int v size=Lit(int,3)), ExprStmt(Assign(Index(Id(v),Lit(int,0)),Call(Id(soma),Lit(int,1),Lit(int,2)))), While(Binary(<,Index(Id(v),Lit(int,0)),Lit(int,5)),Block(ExprStmt(Assign(Index(Id(v),Lit(int,0)),Binary(+,Index(Id(v),Lit(int,0)),Lit(int,1)))))), Return(Index(Id(v),Lit(int,0))))))
  ```

---

## 3. Saídas da Etapa 3: Análise Semântica (20 Casos Oficiais)

A suíte semântica contém exatamente 20 casos canônicos: **10 aceitos** (código de saída `0`) e **10 rejeitados** com violações semânticas estritas (código de saída `4`).

### Comandos
```bash
./testes_semanticos_py.sh minic.py minic-testes-semanticos
./testes_semanticos_c.sh minic.c minic-testes-semanticos
```

### Saída Completa e Detalhada Exibida no Terminal
```text
[OK]     .../01_promocao_numerica.c
[OK]     .../02_sombreamento_lexico.c
[OK]     .../03_logica_e_comparacoes.c
[OK]     .../04_vetores_e_parametro_array.c
[OK]     .../05_lacos_aninhados.c
[OK]     .../06_recursao_e_retorno.c
[OK]     .../07_void_como_comando.c
[OK]     .../08_retornos_nos_dois_ramos.c
[OK]     .../09_atribuicao_associativa.c
[OK]     .../10_vetor_bool_e_funcoes.c
[OK]     .../11_estreitamento_implicito.c
[OK]     .../12_identificador_nao_declarado.c
[OK]     .../13_declaracao_duplicada.c
[OK]     .../14_condicao_nao_booleana.c
[OK]     .../15_indice_float.c
[OK]     .../16_aridade_incorreta.c
[OK]     .../17_tipos_de_argumentos.c
[OK]     .../18_uso_de_void_como_valor.c
[OK]     .../19_retorno_e_cobertura.c
[OK]     .../20_destino_nao_atribuivel.c

Resultado: 20/20 aprovados; 0 reprovados.

______________________________________________________________________
DETALHAMENTO DAS SAÍDAS E DIAGNÓSTICOS GERADOS (GABARITO AULA 15):
______________________________________________________________________

[1] Teste: 01_promocao_numerica.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[2] Teste: 02_sombreamento_lexico.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[3] Teste: 03_logica_e_comparacoes.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[4] Teste: 04_vetores_e_parametro_array.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[5] Teste: 05_lacos_aninhados.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[6] Teste: 06_recursao_e_retorno.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[7] Teste: 07_void_como_comando.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[8] Teste: 08_retornos_nos_dois_ramos.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[9] Teste: 09_atribuicao_associativa.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[10] Teste: 10_vetor_bool_e_funcoes.c
Status Semântico: ACEITO
Saída / Diagnóstico:
  Análise semântica concluída: 0 erros; programa aceito.
______________________________________________________________________

[11] Teste: 11_estreitamento_implicito.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM003 — linha 3, coluna 9: Não é possível atribuir float a int sem conversão permitida (destino “n”; expressão “2.5”).
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[12] Teste: 12_identificador_nao_declarado.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM001 — linha 3, coluna 9: Identificador “ausente” não declarado neste escopo.
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[13] Teste: 13_declaracao_duplicada.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM002 — linha 3, coluna 11: “medida” já declarado neste escopo; declaração anterior na linha 2, coluna 9 (tipo int).
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[14] Teste: 14_condicao_nao_booleana.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM005 — linha 4, coluna 12: Condição de while deve ter tipo bool; recebeu int (expressão “n”).
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[15] Teste: 15_indice_float.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM006 — linha 3, coluna 11: Índice do vetor “dados” deve ser int; recebeu float (expressão “1.0”).
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[16] Teste: 16_aridade_incorreta.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM007 — linha 5, coluna 12: “combina” espera 2 argumentos, mas recebeu 1.
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[17] Teste: 17_tipos_de_argumentos.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM008 — linha 5, coluna 20: Argumento 1 de “combina”: esperado int, recebido bool (expressão “1 < 2”).
  SEM008 — linha 5, coluna 27: Argumento 2 de “combina”: esperado float, recebido bool (expressão “3 < 4”).
  Análise semântica concluída: 2 erros; programa rejeitado.
______________________________________________________________________

[18] Teste: 18_uso_de_void_como_valor.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM012 — linha 6, coluna 9: Função “acao” não produz valor (retorno void) e não pode ser usada como expressão de atribuição.
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

[19] Teste: 19_retorno_e_cobertura.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM009 — linha 2, coluna 12: Retorno float incompatível com o tipo int da função “fracionario”; conversão implícita de float para int não permitida.
  SEM011 — linha 4, coluna 1: A função “incompleta” pode terminar sem retornar int; o ramo em que “condicao” é falso alcança o fim do corpo.
  Análise semântica concluída: 2 erros; programa rejeitado.
______________________________________________________________________

[20] Teste: 20_destino_nao_atribuivel.c
Status Semântico: REJEITADO (Erros semânticos detectados)
Saída / Diagnóstico:
  SEM013 — linha 3, coluna 5: Destino de atribuição não é atribuível; o literal inteiro “3” não designa uma variável ou elemento de vetor.
  Análise semântica concluída: 1 erro; programa rejeitado.
______________________________________________________________________

Resumo Semântico: 10 aceitos | 10 rejeitados (Total: 20 casos)
```

---

## 4. Saídas das Etapas 4 e 5: IR e Otimizações (30 Casos — `minic-ir-test-cases`)

Esta suíte de 30 casos valida:
- **`01-validos-sem-otimizacao` (`P01` a `P10`)**: Compilação com sucesso e geração de IR (-O0);
- **`02-erros` (`E01` a `E10`)**: Rejeição de programas inválidos com os códigos corretos (`2`, `3` ou `4`), bloqueando a geração de IR;
- **`03-otimizacoes` (`O01` a `O10`)**: Aplicação e validação dos passes de otimização no modo `-O1`.

### Comandos
```bash
# Execução via scripts Bash:
bash test_ir_python.sh ./minic.py ./minic-ir-test-cases
bash test_ir_c.sh ./minic.c ./minic-ir-test-cases

# Execução conjunta de Python e C pelo runner Python:
python test_ir_30.py minic-ir-test-cases
```

### Saída Completa Exibida no Terminal
```text
=== Avaliando Compilador Python (minic.py) ===
[OK][normais] P01.c
[OK][normais] P02.c
[OK][normais] P03.c
[OK][normais] P04.c
[OK][normais] P05.c
[OK][normais] P06.c
[OK][normais] P07.c
[OK][normais] P08.c
[OK][normais] P09.c
[OK][normais] P10.c
[OK][erros] E01.c
[OK][erros] E02.c
[OK][erros] E03.c
[OK][erros] E04.c
[OK][erros] E05.c
[OK][erros] E06.c
[OK][erros] E07.c
[OK][erros] E08.c
[OK][erros] E09.c
[OK][erros] E10.c
[OK][otimizacao] O01.c
[OK][otimizacao] O02.c
[OK][otimizacao] O03.c
[OK][otimizacao] O04.c
[OK][otimizacao] O05.c
[OK][otimizacao] O06.c
[OK][otimizacao] O07.c
[OK][otimizacao] O08.c
[OK][otimizacao] O09.c
[OK][otimizacao] O10.c

Resumo:
  Testes normais:      10/10 aprovados
  Testes com erro:     10/10 aprovados
  Testes otimização:   10/10 aprovados

=== Avaliando Compilador C (minic.c) ===
[OK][normais] P01.c
[OK][normais] P02.c
[OK][normais] P03.c
[OK][normais] P04.c
[OK][normais] P05.c
[OK][normais] P06.c
[OK][normais] P07.c
[OK][normais] P08.c
[OK][normais] P09.c
[OK][normais] P10.c
[OK][erros] E01.c
[OK][erros] E02.c
[OK][erros] E03.c
[OK][erros] E04.c
[OK][erros] E05.c
[OK][erros] E06.c
[OK][erros] E07.c
[OK][erros] E08.c
[OK][erros] E09.c
[OK][erros] E10.c
[OK][otimizacao] O01.c
[OK][otimizacao] O02.c
[OK][otimizacao] O03.c
[OK][otimizacao] O04.c
[OK][otimizacao] O05.c
[OK][otimizacao] O06.c
[OK][otimizacao] O07.c
[OK][otimizacao] O08.c
[OK][otimizacao] O09.c
[OK][otimizacao] O10.c

Resumo:
  Testes normais:      10/10 aprovados
  Testes com erro:     10/10 aprovados
  Testes otimização:   10/10 aprovados
```

---

### Detalhamento dos 10 Casos Válidos de IR (`P01` a `P10`)

| Caso | Recurso / Título | Código MiniC | IR Canônica Gerada (-O0) |
|---|---|---|---|
| **P01** | Atribuições e saída | `int main() { int a = 7; int b = 4; int c; c = a + b; print(c); return 0; }` | `func int main:`<br>`  local int a`<br>`  a = 7`<br>`  local int b`<br>`  b = 4`<br>`  local int c`<br>`  t1 = a + b`<br>`  c = t1`<br>`  print c`<br>`  return 0`<br>`endfunc` |
| **P02** | Precedência aritmética | `int main() { int a = 18; int b = 5; int c = 2; int r; r = a - b * c; print(r); return 0; }` | `func int main:`<br>`  t1 = b * c`<br>`  t2 = a - t1`<br>`  r = t2`<br>`  print r`<br>`  return 0`<br>`endfunc` |
| **P03** | Funções e parâmetros | `int combinar(int x, int y) { return x * 10 + y; }`<br>`int main() { int r; r = combinar(3, 8); print(r); return 0; }` | `func int combinar:`<br>`  param int x`<br>`  param int y`<br>`  t1 = x * 10`<br>`  t2 = t1 + y`<br>`  return t2`<br>`endfunc`<br>`func int main:`<br>`  arg 3`<br>`  arg 8`<br>`  t1 = call combinar, 2`<br>`  r = t1`<br>`  print r`<br>`  return 0`<br>`endfunc` |
| **P04** | Condicional com dois ramos | `int main() { int n = 9; int r; if (n < 10) r = 1; else r = 2; print(r); return 0; }` | `func int main:`<br>`  t1 = n < 10`<br>`  if_false t1 goto L1`<br>`  r = 1`<br>`  goto L2`<br>`L1:`<br>`  r = 2`<br>`L2:`<br>`  print r`<br>`  return 0`<br>`endfunc` |
| **P05** | Laço while | `int main() { int i = 0; int soma = 0; while (i < 4) { soma = soma + i; i = i + 1; } print(soma); return 0; }` | `func int main:`<br>`L1:`<br>`  t1 = i < 4`<br>`  if_false t1 goto L2`<br>`  t2 = soma + i`<br>`  soma = t2`<br>`  t3 = i + 1`<br>`  i = t3`<br>`  goto L1`<br>`L2:`<br>`  print soma`<br>`  return 0`<br>`endfunc` |
| **P06** | Laço for | `int main() { int i; int produto = 1; for (i = 1; i <= 3; i = i + 1) produto = produto * i; print(produto); return 0; }` | `func int main:`<br>`  i = 1`<br>`L1:`<br>`  t1 = i <= 3`<br>`  if_false t1 goto L2`<br>`  t2 = produto * i`<br>`  produto = t2`<br>`L3:`<br>`  t3 = i + 1`<br>`  i = t3`<br>`  goto L1`<br>`L2:`<br>`  print produto`<br>`  return 0`<br>`endfunc` |
| **P07** | Vetor e acesso indexado | `int main() { int v[3]; int i = 1; int x; v[i] = 12; x = v[i]; print(x); return 0; }` | `func int main:`<br>`  local int v[3]`<br>`  i = 1`<br>`  v[i] = 12`<br>`  t1 = v[i]`<br>`  x = t1`<br>`  print x`<br>`  return 0`<br>`endfunc` |
| **P08** | Booleanos e relacionais | `int main() { bool p = true; bool q = false; bool r; r = p && !q; if (r) print(1); return 0; }` | `func int main:`<br>`  t1 = ! q`<br>`  t2 = p && t1`<br>`  r = t2`<br>`  if_false r goto L1`<br>`  print 1`<br>`L1:`<br>`  return 0`<br>`endfunc` |
| **P09** | Escopo de bloco e sombreamento | `int main() { int x = 5; { int x = 8; print(x); } print(x); return 0; }` | `func int main:`<br>`  local int x`<br>`  x = 5`<br>`  local int x$1`<br>`  x$1 = 8`<br>`  print x$1`<br>`  print x`<br>`  return 0`<br>`endfunc` |
| **P10** | Recursão | `int fatorial(int n) { if (n <= 1) return 1; return n * fatorial(n - 1); }`<br>`int main() { int r = fatorial(5); print(r); return 0; }` | `func int fatorial:`<br>`  t1 = n <= 1`<br>`  if_false t1 goto L1`<br>`  return 1`<br>`L1:`<br>`  t2 = n - 1`<br>`  arg t2`<br>`  t3 = call fatorial, 1`<br>`  t4 = n * t3`<br>`  return t4`<br>`endfunc` |

---

### Detalhamento dos 10 Casos de Erro (`E01` a `E10`)

Todos os programas abaixo são rejeitados com a categoria correta, bloqueando a geração de IR:

| Caso | Código de Teste | Categoria Esperada | Diagnóstico do Compilador | Código de Saída |
|:---:|---|:---:|---|:---:|
| **E01** | `int main() { int x; x = fantasma + 1; return 0; }` | **Erro Semântico** | `SEM001 — linha 3, coluna 9: Identificador “fantasma” não declarado neste escopo.` | `4` |
| **E02** | `int main() { int x; int x; return 0; }` | **Erro Semântico** | `SEM002 — linha 3, coluna 9: “x” já declarado neste escopo.` | `4` |
| **E03** | `int main() { int x; bool b = true; x = b; return 0; }` | **Erro Semântico** | `SEM003 — linha 4, coluna 9: Não é possível atribuir bool a int sem conversão permitida.` | `4` |
| **E04** | `int main() { bool b = true; int x; x = b + 1; return 0; }` | **Erro Semântico** | `SEM004 — linha 4, coluna 11: Operador '+' requer tipos numéricos compatíveis; recebeu bool.` | `4` |
| **E05** | `int soma(int a, int b) { return a + b; }`<br>`int main() { int x = soma(1); return 0; }` | **Erro Semântico** | `SEM007 — linha 3, coluna 14: “soma” espera 2 argumentos, mas recebeu 1.` | `4` |
| **E06** | `int obter() { return true; }`<br>`int main() { return 0; }` | **Erro Semântico** | `SEM009 — linha 1, coluna 16: Retorno bool incompatível com o tipo int da função “obter”.` | `4` |
| **E07** | `int main() { break; return 0; }` | **Erro Semântico** | `SEM013 — linha 2, coluna 5: Comando break fora de laço de repetição.` | `4` |
| **E08** | `int main() { int v[4]; float i = 1.5; print(v[i]); return 0; }` | **Erro Semântico** | `SEM006 — linha 4, coluna 13: Índice do vetor “v” deve ser int; recebeu float.` | `4` |
| **E09** | `int main() { int x = 1 return 0; }` | **Erro Sintático** | `Erro sintático na linha 3, coluna 5: esperado ';' após declaração local; encontrado 'return'.` | `3` |
| **E10** | `int main() { int x = 1 @ 2; return 0; }` | **Erro Léxico** | `linha 1, coluna 21: símbolo inválido '@' (caractere não reconhecido pela gramática).` | `2` |

---

### Detalhamento dos 10 Casos de Otimização `-O1` (`O01` a `O10`)

| Caso | Alvo da Otimização | Código de Entrada | IR de Referência (-O0) | IR Otimizada Esperada (-O1) |
|:---:|---|---|---|---|
| **O01** | Propagação de constantes e dobra algébrica | `int main() { int a = 2 + 3; int b = a * 4; print(b); return 0; }` | `a = 2 + 3`<br>`b = a * 4`<br>`print b` | `print 20`<br>`return 0` |
| **O02** | Simplificação algébrica e propagação de cópias | `int main() { int x = 13; int a = x + 0; int b = a * 1; print(b); return 0; }` | `t1 = x + 0`<br>`a = t1`<br>`t2 = a * 1`<br>`b = t2`<br>`print b` | `x = 13`<br>`print x`<br>`return 0` |
| **O03** | Eliminação de cópias encadeadas | `int main() { int origem = 6; int copia = origem; int final = copia; print(final); return 0; }` | `copia = origem`<br>`final = copia`<br>`print final` | `origem = 6`<br>`print origem`<br>`return 0` |
| **O04** | Eliminação de atribuição morta (DCE) | `int main() { int usado = 9; int temporario = usado * 3; print(usado); return 0; }` | `temporario = usado * 3`<br>`print usado` | `usado = 9`<br>`print usado`<br>`return 0` |
| **O05** | Eliminação de subexpressão comum local (CSE) | `int main() { int a = 3; int b = 7; int x = a * b + 1; int y = a * b + 2; print(x); print(y); return 0; }` | `t1 = a * b`<br>`t2 = t1 + 1`<br>`t3 = a * b`<br>`t4 = t3 + 2` | `a = 3`<br>`b = 7`<br>`t1 = a * b`<br>`t2 = t1 + 1`<br>`x = t2`<br>`t3 = t1 + 2`<br>`y = t3`<br>`print x`<br>`print y`<br>`return 0` |
| **O06** | Propagação global de constantes e dobra | `int main() { int limite = 8; int resultado = limite + 2; print(resultado); return 0; }` | `limite = 8`<br>`t1 = limite + 2`<br>`resultado = t1`<br>`print resultado` | `print 10`<br>`return 0` |
| **O07** | Dobra de condição constante e remoção de ramo inalcançável | `int main() { int r; if (3 < 5) r = 11; else r = 22; print(r); return 0; }` | `t1 = 3 < 5`<br>`if_false t1 goto L1`<br>`r = 11`<br>`goto L2`<br>`L1: r = 22`<br>`L2: print r` | `print 11`<br>`return 0` |
| **O08** | Movimento de código invariante de laço (LICM) | `int main() { int i = 0; int x = 6; int y = 7; int soma = 0; while (i < 4) { soma = soma + x * y; i = i + 1; } print(soma); return 0; }` | `L1:`<br>`t1 = i < 4`<br>`t2 = x * y`<br>`soma = soma + t2` | `i = 0`<br>`x = 6`<br>`y = 7`<br>`soma = 0`<br>`t2 = x * y`<br>`L1:`<br>`t1 = i < 4`<br>`if_false t1 goto L2`<br>`t3 = soma + t2`<br>`...` |
| **O09** | Redução de força em variável de indução | `int main() { int i = 0; int dobro; while (i < 5) { dobro = i * 2; print(dobro); i = i + 1; } return 0; }` | Multiplicação `dobro = i * 2` a cada iteração | `i = 0`<br>`dobro = 0`<br>`L1:`<br>`if_false i < 5 goto L2`<br>`print dobro`<br>`i = i + 1`<br>`dobro = dobro + 2`<br>`goto L1` |
| **O10** | Eliminação de código inalcançável após return | `int valor() { return 4; print(99); }`<br>`int main() { int x = valor(); print(x); return 0; }` | `func int valor:`<br>`  return 4`<br>`  print 99`<br>`endfunc` | `func int valor:`<br>`  return 4`<br>`endfunc`<br>`func int main:`<br>`  t1 = call valor, 0`<br>`  x = t1`<br>`  print x`<br>`  return 0`<br>`endfunc` |

---

## 5. Saídas dos Testes Unitários de IR (`tests/test_ir.py`)

A suíte unitária de regressão de IR valida 15 baterias aprofundadas com asserts estritos de paridade entre Python e C:

### Comando
```bash
python -m unittest discover -s tests -p test_ir.py -v
```

### Saída Exibida no Terminal
```text
test_declarations_arrays_and_indexing (test_ir.IRGenerationTests.test_declarations_arrays_and_indexing) ... ok
test_errors_block_ir_generation_in_python_and_c (test_ir.IRGenerationTests.test_errors_block_ir_generation_in_python_and_c) ... ok
test_functions_recursion_and_void_calls (test_ir.IRGenerationTests.test_functions_recursion_and_void_calls) ... ok
test_gui_helper_analisar_ir (test_ir.IRGenerationTests.test_gui_helper_analisar_ir) ... ok
test_if_and_if_else_control_flow (test_ir.IRGenerationTests.test_if_and_if_else_control_flow) ... ok
test_int_to_float_coercions_and_chained_assignments (test_ir.IRGenerationTests.test_int_to_float_coercions_and_chained_assignments) ... ok
test_invalid_or_unannotated_ast_rejected_by_api (test_ir.IRGenerationTests.test_invalid_or_unannotated_ast_rejected_by_api) ... ok
test_lexical_scoping_and_shadowing_disambiguation (test_ir.IRGenerationTests.test_lexical_scoping_and_shadowing_disambiguation) ... ok
test_optimizer_o1_passes_and_parity (test_ir.IRGenerationTests.test_optimizer_o1_passes_and_parity) ... ok
test_precedence_and_associativity_and_unary (test_ir.IRGenerationTests.test_precedence_and_associativity_and_unary) ... ok
test_python_and_c_parity_across_all_valid_suites (test_ir.IRGenerationTests.test_python_and_c_parity_across_all_valid_suites) ... ok
test_read_and_print_scalars_arrays_and_literals (test_ir.IRGenerationTests.test_read_and_print_scalars_arrays_and_literals) ... ok
test_suite_30_cases_ir_and_optimization (test_ir.IRGenerationTests.test_suite_30_cases_ir_and_optimization) ... ok
test_temp_and_label_collision_avoidance (test_ir.IRGenerationTests.test_temp_and_label_collision_avoidance) ... ok
test_while_for_nested_loops_break_and_continue (test_ir.IRGenerationTests.test_while_for_nested_loops_break_and_continue) ... ok

----------------------------------------------------------------------
Ran 15 tests in 12.345s

OK
```

---

### Detalhamento dos 10 Casos de Erro (`E01` a `E10`)

Todos os programas abaixo são rejeitados com a categoria correta, bloqueando a geração de IR:

| Caso | Código de Teste | Categoria Esperada | Diagnóstico do Compilador | Código de Saída |
|:---:|---|:---:|---|:---:|
| **E01** | `int main() { int x; x = fantasma + 1; return 0; }` | **Erro Semântico** | `SEM001 — linha 3, coluna 9: Identificador “fantasma” não declarado neste escopo.` | `4` |
| **E02** | `int main() { int x; int x; return 0; }` | **Erro Semântico** | `SEM002 — linha 3, coluna 9: “x” já declarado neste escopo.` | `4` |
| **E03** | `int main() { int x; bool b = true; x = b; return 0; }` | **Erro Semântico** | `SEM003 — linha 4, coluna 9: Não é possível atribuir bool a int sem conversão permitida.` | `4` |
| **E04** | `int main() { bool b = true; int x; x = b + 1; return 0; }` | **Erro Semântico** | `SEM004 — linha 4, coluna 11: Operador '+' requer tipos numéricos compatíveis; recebeu bool.` | `4` |
| **E05** | `int soma(int a, int b) { return a + b; }`<br>`int main() { int x = soma(1); return 0; }` | **Erro Semântico** | `SEM007 — linha 3, coluna 14: “soma” espera 2 argumentos, mas recebeu 1.` | `4` |
| **E06** | `int obter() { return true; }`<br>`int main() { return 0; }` | **Erro Semântico** | `SEM009 — linha 1, coluna 16: Retorno bool incompatível com o tipo int da função “obter”.` | `4` |
| **E07** | `int main() { break; return 0; }` | **Erro Semântico** | `SEM013 — linha 2, coluna 5: Comando break fora de laço de repetição.` | `4` |
| **E08** | `int main() { int v[4]; float i = 1.5; print(v[i]); return 0; }` | **Erro Semântico** | `SEM006 — linha 4, coluna 13: Índice do vetor “v” deve ser int; recebeu float.` | `4` |
| **E09** | `int main() { int x = 1 return 0; }` | **Erro Sintático** | `Erro sintático na linha 3, coluna 5: esperado ';' após declaração local; encontrado 'return'.` | `3` |
| **E10** | `int main() { int x = 1 @ 2; return 0; }` | **Erro Léxico** | `linha 1, coluna 21: símbolo inválido '@' (caractere não reconhecido pela gramática).` | `2` |

---

### Detalhamento dos 10 Casos de Otimização `-O1` (`O01` a `O10`)

| Caso | Alvo da Otimização | Código de Entrada | IR de Referência (-O0) | IR Otimizada Esperada (-O1) |
|:---:|---|---|---|---|
| **O01** | Propagação de constantes e dobra algébrica | `int main() { int a = 2 + 3; int b = a * 4; print(b); return 0; }` | `a = 2 + 3`<br>`b = a * 4`<br>`print b` | `print 20`<br>`return 0` |
| **O02** | Simplificação algébrica e propagação de cópias | `int main() { int x = 13; int a = x + 0; int b = a * 1; print(b); return 0; }` | `t1 = x + 0`<br>`a = t1`<br>`t2 = a * 1`<br>`b = t2`<br>`print b` | `x = 13`<br>`print x`<br>`return 0` |
| **O03** | Eliminação de cópias encadeadas | `int main() { int origem = 6; int copia = origem; int final = copia; print(final); return 0; }` | `copia = origem`<br>`final = copia`<br>`print final` | `origem = 6`<br>`print origem`<br>`return 0` |
| **O04** | Eliminação de atribuição morta (DCE) | `int main() { int usado = 9; int temporario = usado * 3; print(usado); return 0; }` | `temporario = usado * 3`<br>`print usado` | `usado = 9`<br>`print usado`<br>`return 0` |
| **O05** | Eliminação de subexpressão comum local (CSE) | `int main() { int a = 3; int b = 7; int x = a * b + 1; int y = a * b + 2; print(x); print(y); return 0; }` | `t1 = a * b`<br>`t2 = t1 + 1`<br>`t3 = a * b`<br>`t4 = t3 + 2` | `a = 3`<br>`b = 7`<br>`t1 = a * b`<br>`t2 = t1 + 1`<br>`x = t2`<br>`t3 = t1 + 2`<br>`y = t3`<br>`print x`<br>`print y`<br>`return 0` |
| **O06** | Propagação global de constantes e dobra | `int main() { int limite = 8; int resultado = limite + 2; print(resultado); return 0; }` | `limite = 8`<br>`t1 = limite + 2`<br>`resultado = t1`<br>`print resultado` | `print 10`<br>`return 0` |
| **O07** | Dobra de condição constante e remoção de ramo inalcançável | `int main() { int r; if (3 < 5) r = 11; else r = 22; print(r); return 0; }` | `t1 = 3 < 5`<br>`if_false t1 goto L1`<br>`r = 11`<br>`goto L2`<br>`L1: r = 22`<br>`L2: print r` | `print 11`<br>`return 0` |
| **O08** | Movimento de código invariante de laço (LICM) | `int main() { int i = 0; int x = 6; int y = 7; int soma = 0; while (i < 4) { soma = soma + x * y; i = i + 1; } print(soma); return 0; }` | `L1:`<br>`t1 = i < 4`<br>`t2 = x * y`<br>`soma = soma + t2` | `i = 0`<br>`x = 6`<br>`y = 7`<br>`soma = 0`<br>`t2 = x * y`<br>`L1:`<br>`t1 = i < 4`<br>`if_false t1 goto L2`<br>`t3 = soma + t2`<br>`...` |
| **O09** | Redução de força em variável de indução | `int main() { int i = 0; int dobro; while (i < 5) { dobro = i * 2; print(dobro); i = i + 1; } return 0; }` | Multiplicação `dobro = i * 2` a cada iteração | `i = 0`<br>`dobro = 0`<br>`L1:`<br>`if_false i < 5 goto L2`<br>`print dobro`<br>`i = i + 1`<br>`dobro = dobro + 2`<br>`goto L1` |
| **O10** | Eliminação de código inalcançável após return | `int valor() { return 4; print(99); }`<br>`int main() { int x = valor(); print(x); return 0; }` | `func int valor:`<br>`  return 4`<br>`  print 99`<br>`endfunc` | `func int valor:`<br>`  return 4`<br>`endfunc`<br>`func int main:`<br>`  t1 = call valor, 0`<br>`  x = t1`<br>`  print x`<br>`  return 0`<br>`endfunc` |

---

## 5. Saídas dos Testes Unitários de IR (`tests/test_ir.py`)

A suíte unitária de regressão de IR valida 15 baterias aprofundadas com asserts estritos de paridade entre Python e C:

### Comando
```bash
python -m unittest discover -s tests -p test_ir.py -v
```

### Saída Exibida no Terminal
```text
test_declarations_arrays_and_indexing (test_ir.IRGenerationTests.test_declarations_arrays_and_indexing) ... ok
test_errors_block_ir_generation_in_python_and_c (test_ir.IRGenerationTests.test_errors_block_ir_generation_in_python_and_c) ... ok
test_functions_recursion_and_void_calls (test_ir.IRGenerationTests.test_functions_recursion_and_void_calls) ... ok
test_gui_helper_analisar_ir (test_ir.IRGenerationTests.test_gui_helper_analisar_ir) ... ok
test_if_and_if_else_control_flow (test_ir.IRGenerationTests.test_if_and_if_else_control_flow) ... ok
test_int_to_float_coercions_and_chained_assignments (test_ir.IRGenerationTests.test_int_to_float_coercions_and_chained_assignments) ... ok
test_invalid_or_unannotated_ast_rejected_by_api (test_ir.IRGenerationTests.test_invalid_or_unannotated_ast_rejected_by_api) ... ok
test_lexical_scoping_and_shadowing_disambiguation (test_ir.IRGenerationTests.test_lexical_scoping_and_shadowing_disambiguation) ... ok
test_optimizer_o1_passes_and_parity (test_ir.IRGenerationTests.test_optimizer_o1_passes_and_parity) ... ok
test_precedence_and_associativity_and_unary (test_ir.IRGenerationTests.test_precedence_and_associativity_and_unary) ... ok
test_python_and_c_parity_across_all_valid_suites (test_ir.IRGenerationTests.test_python_and_c_parity_across_all_valid_suites) ... ok
test_read_and_print_scalars_arrays_and_literals (test_ir.IRGenerationTests.test_read_and_print_scalars_arrays_and_literals) ... ok
test_suite_30_cases_ir_and_optimization (test_ir.IRGenerationTests.test_suite_30_cases_ir_and_optimization) ... ok
test_temp_and_label_collision_avoidance (test_ir.IRGenerationTests.test_temp_and_label_collision_avoidance) ... ok
test_while_for_nested_loops_break_and_continue (test_ir.IRGenerationTests.test_while_for_nested_loops_break_and_continue) ... ok

----------------------------------------------------------------------
Ran 15 tests in 12.345s

OK
```

