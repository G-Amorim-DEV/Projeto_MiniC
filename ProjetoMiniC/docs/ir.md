# Representação Intermediária (IR) — Código de Três Endereços (TAC)

A etapa de geração de Representação Intermediária (IR) consome a AST validada e anotada pelo analisador semântico (`SemanticAnalyzer` em Python e `semantic_analyze` em C) e produz **Código de Três Endereços (TAC)** textual, explícito e determinístico, com paridade exata entre as implementações em Python e C.

## Pipeline de Compilação

```text
Código-Fonte (.c / .minic)
  → Analisador Léxico (Scanner)         [código de saída 2 em caso de erro]
  → Analisador Sintático (Parser / AST) [código de saída 3 em caso de erro]
  → Analisador Semântico                [código de saída 4 em caso de erro]
  → Gerador de IR (TAC)                 [código de saída 0 em caso de sucesso]
```

O gerador de IR **não executa** caso haja qualquer erro léxico, sintático ou semântico nas etapas anteriores. Além disso, a API (`generate_ir` em Python e `ir_generate` em C) valida estruturalmente a AST recebida e recusa árvores vazias, não anotadas pela análise semântica ou contendo nós marcados com `<error>`.

## Como Executar

A partir da raiz do repositório:

```bash
# Python (via minic.py, main.py, ir.py ou módulo)
python3 minic.py --ir arquivo.c
python3 main.py arquivo.c --ir
python3 ir.py arquivo.c
python3 -m ProjetoMiniC.src.ir arquivo.c
python3 -m ProjetoMiniC.src.ir              # abre a interface gráfica (Tkinter) do IR

# C (via Makefile ou compilação direta com GCC)
make semantic
./minic --ir arquivo.c

make ir
./ir arquivo.c

# Compilação em arquivo único (compatível com scripts de correção):
gcc -std=c11 -Wall -Wextra -pedantic -O2 minic.c -o minic
./minic --ir arquivo.c

gcc -std=c11 -Wall -Wextra -pedantic -O2 ir.c -o ir
./ir arquivo.c
```

## Conjunto de Instruções TAC

As instruções dentro do corpo de funções são indentadas com dois espaços (`  `); diretivas de nível de módulo (`global`, `func`, `endfunc`) ficam na coluna `0`.

| Categoria | Formato Textual TAC | Descrição |
|---|---|---|
| Declaração global escalar | `global <tipo> <nome>` | Declara variável escalar no escopo global (`escopo 0`). |
| Declaração global vetor | `global <tipo> <nome>[<tam>]` | Declara vetor global com dimensão `<tam>`. |
| Cabeçalho de função | `func <tipo_retorno> <nome>:` | Inicia a definição da função `<nome>`. |
| Fim de função | `endfunc` | Encerra a definição da função atual. |
| Parâmetro formal | `param <tipo> <nome_ir>` | Declara parâmetro formal escalar (`<tipo>`) ou vetor (`<tipo>[]`). |
| Declaração local escalar | `local <tipo> <nome_ir>` | Declara variável escalar local. |
| Declaração local vetor | `local <tipo> <nome_ir>[<tam>]` | Declara vetor local com dimensão `<tam>`. |
| Cópia / Atribuição | `<dest> = <orig>` | Copia o valor de `<orig>` para `<dest>`. |
| Operação unária | `<temp> = <op> <arg>` | Operadores `-` (negação aritmética), `!` (negação lógica) e `int2float` (promoção implícita `int → float`). |
| Operação binária | `<temp> = <esq> <op> <dir>` | Operadores `+`, `-`, `*`, `/`, `%`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `&&`, `||`. |
| Leitura de vetor | `<temp> = <vetor>[<indice>]` | Carrega o elemento de `<vetor>` na posição `<indice>` em `<temp>`. |
| Escrita em vetor | `<vetor>[<indice>] = <valor>` | Armazena `<valor>` na posição `<indice>` de `<vetor>`. |
| Rótulo | `L<n>:` | Define ponto de destino para desvios de controle de fluxo. |
| Desvio incondicional | `goto L<n>` | Transfere o fluxo de controle para o rótulo `L<n>`. |
| Desvio condicional | `if_false <cond> goto L<n>` | Desvia para `L<n>` se a expressão booleana `<cond>` for falsa. |
| Passagem de argumento | `arg <valor>` | Empilha/prepara `<valor>` para a próxima chamada de função. |
| Chamada com retorno | `<temp> = call <func>, <n>` | Invoca `<func>` com `<n>` argumentos e armazena o retorno em `<temp>`. |
| Chamada `void` | `call <func>, <n>` | Invoca função de retorno `void` com `<n>` argumentos. |
| Retorno de função | `return` ou `return <valor>` | Encerra a execução da função (com ou sem valor). |
| Saída (`print`) | `print <valor>` | Imprime o valor avaliado. |
| Entrada (`read`) | `read <var>` ou `read <vetor>[<indice>]` | Lê valor da entrada padrão para variável escalar ou posição de vetor. |

## Regras de Tradução

### 1. Temporários e Rótulos
- Temporários são numerados sequencialmente na ordem de avaliação da AST: `t1`, `t2`, `t3`, ...
- Rótulos são numerados sequencialmente na ordem de construção das estruturas de desvio: `L1`, `L2`, `L3`, ...

### 2. Escopos e Desambiguação de Identificadores
O analisador semântico associa cada uso de identificador (`Id` / `Index`) à sua declaração exata e ao número determinístico de seu escopo léxico (`0` para global, `>= 1` para escopos de função e blocos internos):
- Variáveis globais mantêm seu nome original (`<nome>`).
- Dentro de uma função, a primeira declaração de um identificador que não sombreia uma variável global nem outra declaração anterior na mesma função mantém seu nome original (`<nome>`).
- Qualquer declaração local ou parâmetro que sombreie uma variável global ou outra variável/parâmetro já visto na função recebe o sufixo determinístico `$<escopo>` (por exemplo, `x$1`, `x$2`), evitando colisões de nomes entre escopos distintos.

### 3. Promoções Numéricas (`int → float`)
As anotações `coercion_type = "float"` e `chain_coercion_type = "float"` produzidas pela análise semântica são convertidas em instruções explícitas:
```text
t1 = int2float <operando_int>
```
em inicializações, atribuições simples e associativas (`c = a = b = 2`), operações binárias mistas, passagem de argumentos e comandos `return`.

### 4. Controle de Fluxo e Laços Aninhados
- **`if (cond) then_stmt`** (sem `else`):
  ```text
  <avalia cond em t_c>
  if_false t_c goto L_end
  <then_stmt>
  L_end:
  ```
- **`if (cond) then_stmt else else_stmt`**:
  ```text
  <avalia cond em t_c>
  if_false t_c goto L_else
  <then_stmt>
  goto L_end
  L_else:
  <else_stmt>
  L_end:
  ```
- **`while (cond) body`**:
  ```text
  L_start:
  <avalia cond em t_c>
  if_false t_c goto L_end
  <body (continue -> goto L_start, break -> goto L_end)>
  goto L_start
  L_end:
  ```
- **`for (init; cond; inc) body`**:
  ```text
  <init>
  L_start:
  <avalia cond em t_c>
  if_false t_c goto L_end
  <body (continue -> goto L_step, break -> goto L_end)>
  L_step:
  <inc>
  goto L_start
  L_end:
  ```
Uma pilha de alvos de laço (`(continue_label, break_label)`) garante que `break` e `continue` em laços aninhados sempre desviem para o laço imediatamente envolvente.

## Organização dos Módulos

- **Python (`ProjetoMiniC/src/ir/`)**:
  - `instructions.py`: `IRInstruction`, `IRProgram`, `IRGenerationError`.
  - `generator.py`: `IRGenerator` e `generate_ir(program)`.
  - `printer.py`: `format_instruction(inst)` e `format_ir(program)`.
  - `__main__.py`: interface gráfica Tkinter e CLI (`python3 -m ProjetoMiniC.src.ir`).
- **C (`C/`)**:
  - `C/ir.h` e `C/ir.c`: estruturas `IrInstruction`, `IrProgram` e funções `ir_generate`, `ir_format`, `ir_print`.
  - `C/ir_main.c` e `ir.c`: ponto de entrada dedicado para geração de IR em C.
  - `C/semantic_main.c` e `minic.c`: integração do modo `--ir` ao wrapper principal.

