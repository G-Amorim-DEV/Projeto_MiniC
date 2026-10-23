# Projeto MiniC

Compilador educacional para a linguagem **MiniC**, um subconjunto de C. O projeto possui implementacoes equivalentes em Python e C para o analisador lexico e o analisador sintatico, uma interface grafica em Tkinter, ferramentas de linha de comando e suites de testes para as duas implementacoes.

O objetivo do projeto e construir gradualmente um pipeline de compilacao: leitura do codigo-fonte, analise lexica, analise sintatica, construcao da AST, analise semantica, geracao de representacao intermediaria, otimizacao e geracao de codigo.

## Estado atual

| Etapa | Python | C |
|---|---|---|
| Analise lexica | Implementada | Implementada |
| Analise sintatica e AST | Implementada (50/50 casos) | Implementada (50/50 casos) |
| Analise semantica | Implementada (20/20 casos) | Implementada (20/20 casos) |
| Representacao Intermediaria (IR / TAC) | Implementada | Implementada |
| Otimizacao | Em desenvolvimento | Em desenvolvimento |
| Geracao de codigo | Em desenvolvimento | Em desenvolvimento |

O scanner C escreve tokens JSONL em `stdout` e erros JSONL em `stderr`. Os modulos C principais sao:

- `C/scanner.c` e `C/scanner.h`: varredura do texto-fonte.
- `C/token.c` e `C/token.h`: estrutura dos tokens.
- `C/token_types.c` e `C/token_types.h`: tipos e palavras reservadas.
- `C/errors.c` e `C/errors.h`: erros lexicos.
- `C/util.c` e `C/util.h`: memoria, strings dinamicas e leitura de arquivos.
- `C/main.c`: CLI e serializacao JSONL do scanner.
- `C/parser.c`, `C/parser_main.c`: parser e entrada CLI do parser.
- `C/ast.c` e `C/ast.h`: nos, anotacoes semanticas e serializacao da AST.
- `C/semantic.c`, `C/semantic.h` e `C/semantic_main.c`: analisador semantico e CLI.
- `C/ir.c`, `C/ir.h` e `C/ir_main.c`: gerador e formatador de Representacao Intermediaria (TAC) e CLI.

O `Makefile` tambem compila os modulos C separadamente. A unidade `scanner.c` da raiz e destinada aos scripts que compilam um unico arquivo; a pasta `C/` preserva a organizacao modular usada pelo Makefile.

## Testes oficiais do professor

O pacote `testes-parser-50` possui 50 casos:

- casos 01 a 25: devem ser aceitos e produzir a AST esperada;
- casos 26 a 50: devem ser rejeitados com erro sintatico.

Cada caso possui um `codigo.c` e, nos casos validos, um `ast.esperada.txt`. O runner tambem usa `manifesto.json` para mostrar titulo e diretorio na tabela.

### Comando combinado

Executa os parsers Python e C. A tabela e exibida uma vez usando os resultados do Python; o resultado C tambem e validado e qualquer falha faz o comando terminar com codigo diferente de zero.

```bash
bash testar_parser.sh ./testes-parser-50
```

### Parser Python

```bash
bash testar_parser_python.sh ./testes-parser-50 ./parser.py
```

### Parser C

```bash
bash testar_parser_c.sh ./testes-parser-50 ./parser.c
```

Os tres comandos procuram automaticamente `casos` tanto em:

```text
testes-parser-50/casos
```

quanto na estrutura aninhada distribuida:

```text
testes-parser-50/testes-parser-50/casos
```

### Saida esperada

Os runners exibem a tabela oficial neste formato:

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

O codigo de saida esperado e `0`:

```bash
echo $?
```

### Comandos usados pelo professor

Na raiz do projeto, os comandos automatizados sao exatamente:

```bash
bash testar_parser.sh ./testes-parser-50
bash testar_parser_python.sh ./testes-parser-50 ./parser.py
bash testar_parser_c.sh ./testes-parser-50 ./parser.c
```

Cada runner individual imprime o cabecalho, as 50 linhas de resultado e o resumo. O runner combinado executa Python e C, mas imprime uma unica tabela para evitar duplicacao da saida.

Qualquer AST divergente, caso valido rejeitado, caso invalido aceito, falta de ferramenta ou quantidade diferente de 50 casos retorna codigo diferente de zero.

### Runner Python direto

Tambem e possivel executar o runner diretamente:

```bash
python test_parser_50.py "C:\caminho\testes-parser-50\testes-parser-50\casos"
```

Para executar um binario C com a mesma tabela:

```bash
python test_parser_50.py "C:\caminho\testes-parser-50\testes-parser-50\casos" --native .\parser.exe
```

## Testes de regressao do projeto

Com Python:

```bash
python -m unittest discover -s tests -v
```

Com Make, quando `make` estiver disponivel:

```bash
make test-parser
```

Os testes verificam gramatica, precedencia, associatividade, declaracoes, vetores, funcoes, parametros, controle de fluxo, entrada e saida, chamadas, indexacao, erros lexicos, erros sintaticos e paridade da AST entre Python e C.

## Testes do lexer

O scanner Python pode produzir tokens e erros em JSONL:

```bash
python main.py caminho/para/arquivo.minic --jsonl
```

O scanner C pode ser compilado e executado com:

```bash
make
./C/minic_scanner caminho/para/arquivo.c --jsonl
```

Casos internos do lexer ficam em:

- `ProjetoMiniC/casos-programas-c/`: programas validos;
- `ProjetoMiniC/casos-invalidos/`: entradas com erros lexicos intencionais.

Com Make:

```bash
make test-valid
make test-invalid
make test
```

### Testes por fixtures JSONL

Os scripts `test_scanner_python.sh` e `test_scanner_c.sh` percorrem arquivos `.expected.jsonl`, executam o scanner correspondente e comparam a sequencia de tokens gerada com os fixtures. Os casos lexicos ficam principalmente em `ProjetoMiniC/casos-invalidos/` e os programas validos ficam em `ProjetoMiniC/casos-programas-c/`.

Exemplos de uso a partir da raiz:

```bash
bash test_scanner_python.sh ./scanner.py ./ProjetoMiniC
bash test_scanner_c.sh ./scanner.c ./ProjetoMiniC
```

O scanner C e compilado para um executavel temporario ou local chamado `scanner`. Os fixtures verificam tokens em JSONL; quando existe um arquivo `.errors.jsonl`, tambem verificam os diagnosticos lexicos esperados.

## Codigos de saida

| Codigo | Significado |
|---:|---|
| 0 | Analise / geracao concluida com sucesso |
| 1 | Uso incorreto ou erro de leitura |
| 2 | Erro lexico |
| 3 | Erro sintatico |
| 4 | Erro semantico |

Os compiladores Python e C seguem esse contrato para a CLI. A interface grafica apresenta os mesmos resultados em suas janelas de Analise Lexica, Analise Sintatica, Analise Semantica e Gerador de IR.

## Documentacao tecnica

- `ProjetoMiniC/docs/README.md`: detalhes da implementacao Python.
- `ProjetoMiniC/docs/gramatica.ebnf`: arquivo reservado para a gramatica EBNF completa; a gramatica usada pelo parser esta implementada em `src/parser/parser.py` e em `C/parser.c`.
- `ProjetoMiniC/docs/especificacao.md`: especificacao lexica executavel, regras de tokens, recuperacao e formato JSONL.
- `ProjetoMiniC/docs/semantica.md`: especificacao, regras e testes da analise semantica em Python e C.
- `ProjetoMiniC/docs/ir.md`: especificacao do Codigo de Tres Enderecos (TAC), instrucoes geradas, escopos e controle de fluxo.
- `ProjetoMiniC/docs/arquitetura.md`: arquitetura geral do pipeline do compilador.
- `testes-parser-50/README.md`: formato e regras do pacote externo.
- `testes-parser-50/EXECUCAO.txt`: comandos minimos por caso.

## Limitacoes atuais

- A analise semantica esta implementada em Python e C e passou nos 20 casos
  fornecidos em ambas as linguagens, com diagnosticos identicos aos gabaritos.
  Veja [documentacao semantica](ProjetoMiniC/docs/semantica.md).
- A geracao de Representacao Intermediaria (IR) em Codigo de Tres Enderecos (TAC)
  esta implementada em Python e C com paridade textual exata para toda a gramatica MiniC.
  Veja [documentacao de IR](ProjetoMiniC/docs/ir.md).
- Os pacotes de otimizacao e geracao de codigo final ainda sao estruturas de organizacao.
- A interface grafica oferece interfaces proprias para Lexer, Parser, Semantica e IR; Otimizador e Gerador de Codigo exibem aviso de desenvolvimento.
- O projeto analisa e representa programas MiniC; ele ainda nao executa os programas nem gera um executavel final.
- O pacote de testes externos valida a AST e a rejeicao sintatica, nao a execucao do programa.

## Limpeza

Para remover objetos, executaveis e arquivos de saida gerados pelo Make:

```bash
make clean
```

Os scripts de teste usam diretorios temporarios para o executavel C e os removem ao terminar.

## Tecnologias

- Python 3.10+.
- Tkinter.
- C11.
- GCC.
- Make.
- Bash.
- JSONL para a troca de tokens e diagnosticos do lexer.
## Executando a versão em Python

Todos os comandos abaixo devem ser executados **a partir da raiz do repositório**.

### Interface gráfica

```bash
python main.py
```

Abre o painel principal, com um botão para cada etapa do compilador. **Análise Léxica** e **Análise Sintática** abrem interfaces próprias; as demais etapas ainda exibem um aviso de "em desenvolvimento".

### Linha de comando

```bash
python main.py arquivo.minic                # análise léxica (tokens + diagnóstico)
python main.py arquivo.minic --tokens       # só a tabela de tokens
python main.py arquivo.minic --errors       # só os erros léxicos
python main.py arquivo.minic --jsonl        # tokens em JSONL (erros em JSONL no stderr)
python main.py arquivo.minic --parse        # roda o parser e informa se há erros sintáticos
python main.py arquivo.minic --ast          # imprime a AST em árvore
python main.py arquivo.minic --ast --sexp   # imprime a AST em S-expression
```

Atalhos por etapa:

```bash
python scanner.py arquivo.minic --jsonl     # apenas o lexer (aceita caminho relativo a ProjetoMiniC/)
python parser.py arquivo.c                  # apenas o parser; imprime a AST em S-expression
```

Exemplo de saída em S-expression:

```text
Program(Function(int main() Block(Return(Lit(int,0)))))
```

Os módulos também podem ser executados como pacote (também a partir da raiz):

```bash
python -m ProjetoMiniC.src.lexer            # interface gráfica do lexer
python -m ProjetoMiniC.src.lexer arquivo.minic --jsonl
python -m ProjetoMiniC.src.parser           # interface gráfica do parser
```

### Códigos de saída

| Código | Significado |
|---|---|
| `0` | Sucesso |
| `1` | Uso incorreto ou arquivo não encontrado/ilegível |
| `2` | Erro léxico |
| `3` | Erro sintático |

### Interfaces gráficas

- **Lexer** (`src/lexer/__main__.py`): executa os testes embutidos, analisa código colado ou aberto de arquivo (`.minic`, `.mc`, `.c`, `.txt`) e mostra a saída formatada, os tokens em JSONL e os erros em JSONL em abas separadas, com opção de copiar o JSONL.
- **Parser** (`src/parser/__main__.py`): permite digitar ou carregar um arquivo, executar o parser e consultar a AST, os diagnósticos com linha/coluna e os tokens reconhecidos.

## Executando a versão em C

O `Makefile` usa caminhos relativos à **raiz** do repositório. Não é mais necessário entrar em `C/`.

```bash
make                                  # compila o scanner em C/minic_scanner
./C/minic_scanner arquivo.c           # saída legível (tabela de tokens + diagnóstico)
./C/minic_scanner arquivo.c --jsonl   # tokens em JSONL no stdout, erros no stderr

make parser                           # compila o parser em ./parser
./parser arquivo.c                    # imprime a AST em S-expression
```

Também é possível compilar o scanner em um único passo, sem o Makefile:

```bash
gcc -std=c11 scanner.c -o scanner
./scanner arquivo.c
```

O parser em C usa os mesmos códigos de saída da tabela acima (`0`, `1`, `2` e `3`). No Windows, o `Makefile` já trata a extensão `.exe` e o comando de remoção.

Para remover binários e arquivos gerados: `make clean`.

## Testes

| Comando (na raiz) | O que faz |
|---|---|
| `make test` | Roda o scanner em C sobre `casos-programas-c/` e `casos-invalidos/` e grava as saídas em `*.out.jsonl` / `*.err.jsonl` (não compara com o esperado). Também há `make test-valid` e `make test-invalid`. |
| `bash test_scanner_python.sh scanner.py ProjetoMiniC/casos-programas-c` | Compara os tokens do scanner Python com os `.expected.jsonl`. |
| `bash test_scanner_c.sh scanner.c ProjetoMiniC/casos-programas-c` | Compila `scanner.c` e compara os tokens do scanner C com os `.expected.jsonl`. |
| `python test_parser_50.py testes-parser-50/testes-parser-50/casos` | Roda os 50 casos do parser (Python). |
| `make test-parser-50 CASES_DIR=testes-parser-50/testes-parser-50/casos` | Mesmo que o anterior, via Makefile. |
| `make test-parser` | Compila o parser em C e roda `tests/test_parser.py` (requer Tkinter). |

Observações:

- Os scripts `test_scanner_*.sh` recebem `[scanner] [pasta-de-testes]` e geram um `output.jsonl` temporário na pasta atual.
- **50 casos do parser:** os casos 01–25 devem ser aceitos com a AST esperada e os casos 26–50 devem ser rejeitados. O runner retorna `0` quando todos passam, `1` quando há falhas e `2` se a pasta de casos não for encontrada. Sem argumento, ele procura em `~/Downloads/testes-parser-50/...` e em `../testes-parser-50/...`, por isso informe o caminho como nos exemplos acima.
- **Parser em C:** alinhado ao formato oficial da AST do Python e aprovado nos **50/50 casos** do pacote `testes-parser-50` (25 casos válidos com AST idêntica ao gabarito e 25 casos inválidos rejeitados com código `3`).

## O que o lexer reconhece

- palavras reservadas, identificadores, números inteiros e reais, operadores e delimitadores;
- strings e caracteres, incluindo casos malformados;
- comentários de linha e de bloco;
- erros léxicos, como símbolos desconhecidos, comentários não terminados, strings/caracteres não terminados, números reais malformados e identificadores iniciados por dígito.

Cada token reconhecido carrega tipo, lexema, atributo (quando aplicável), linha e coluna. A saída pode ser formatada em tabela ou serializada em JSONL, seguindo o mesmo formato nas versões Python e C.

## Análise sintática e AST

O parser consome os `Token` produzidos pelo lexer e constrói uma AST para declarações (globais e locais, inclusive listas separadas por vírgula e vetores), funções e parâmetros, comandos de controle de fluxo, entrada/saída, chamadas, indexação e expressões (com precedência e associatividade). Os nós usados na saída são: `Program`, `Function`, `Block`, `VarDecl`, `If`, `While`, `Return`, `ExprStmt`, `Assign`, `Binary`, `Unary`, `Call`, `Index`, `Id` e `Lit`.

A AST pode ser exibida de duas formas:

- **S-expression** (`parser.py`, `main.py --ast --sexp`): uma linha, no formato usado pelos casos de teste.
- **Árvore indentada** (`main.py --ast`): mais legível para leitura no terminal.

Erros léxicos e sintáticos são reportados com linha e coluna.

## Casos de teste

- `ProjetoMiniC/casos-programas-c/`: programas `.c` válidos (Fibonacci, números primos, média de vetor, menu interativo, controle de temperatura), cada um com o `.expected.jsonl` correspondente.
- `ProjetoMiniC/casos-invalidos/`: trechos `.minic` com erros léxicos propositais, cada um com `.expected.jsonl` (tokens esperados) e `.errors.jsonl` (erros esperados).
- `testes-parser-50/testes-parser-50/casos/`: 50 programas do professor para o parser. Cada pasta tem `codigo.c`, `ast.esperada.txt` e `resultado.esperado.txt`. O `manifesto.json` lista título e diretório de cada caso.

## Documentação

- `ProjetoMiniC/docs/README.md`: notas sobre a implementação do lexer em Python.
- `ProjetoMiniC/docs/gramatica.ebnf`: gramática da linguagem MiniC.
- `ProjetoMiniC/docs/especificacao.md` e `ProjetoMiniC/docs/arquitetura.md`: ainda a serem preenchidos.
- `testes-parser-50/testes-parser-50/README.md`: descrição do pacote de 50 casos.

## Tecnologias

- Python 3 + Tkinter (interface gráfica)
- C11 (gcc, make)
- JSONL como formato de intercâmbio de tokens/erros entre as implementações e os casos de teste

## Análise Semântica (Aula 15)

O analisador semântico valida todas as restrições estáticas da linguagem MiniC após a construção da AST, incluindo escopos léxicos, checagem e coerção de tipos, aridade e fluxo de controle (`SEM001` a `SEM013`).

### Como o Professor Pode e Deve Realizar os Testes

Os testes semânticos oficiais (20 casos de teste canônicos: 10 aceitos e 10 rejeitados) devem ser executados a partir da raiz do repositório utilizando os scripts de teste Bash oficiais fornecidos:

#### 1. Testes em C (compilação automática com GCC):
```bash
./testes_semanticos_c.sh minic.c minic-testes-semanticos
```
*(ou informando o caminho do diretório: `./testes_semanticos_c.sh minic.c "/caminho/para/minic-testes-semanticos"`)*

#### 2. Testes em Python (Python 3.10+):
```bash
./testes_semanticos_py.sh minic.py minic-testes-semanticos
```
*(ou informando o caminho do diretório: `./testes_semanticos_py.sh minic.py "/caminho/para/minic-testes-semanticos"`)*

#### 3. Execução individual de um arquivo:
```bash
# Em Python:
python3 minic.py arquivo.c

# Em C:
gcc -Wall -Wextra minic.c -o minic
./minic arquivo.c
```

Os wrappers `minic.py` e `minic.c` executam o pipeline completo: **Lexer → Parser/AST → Análise Semântica**.
- Se o programa for válido: retorna código `0` e imprime `Análise semântica concluída: 0 erros; programa aceito.`
- Se houver violação semântica: retorna código `4` e imprime os diagnósticos `SEMxxx` ordenados seguidos de `Análise semântica concluída: N erro(s); programa rejeitado.`

---

### Incrementos Realizados nos Scripts de Teste

Os scripts `testes_semanticos_c.sh` e `testes_semanticos_py.sh` preservam **100% da verificação original do professor** (comparações exatas via `diff -u` contra os arquivos `.gabarito`) e trazem os seguintes incrementos:
1. **Detalhamento Caso a Caso:** Apresenta a saída e o diagnóstico exato gerado pelo compilador para cada um dos 20 testes.
2. **Classificação Semântica Explícita:** Indica se cada teste teve status **ACEITO** ou **REJEITADO**.
3. **Divisórias Visuais:** Linhas demarcadoras (`______________________________________________________________________`) para legibilidade e clareza no terminal.
4. **Resumo Semântico Final:** Contabilização final confirmando exatamente `10 aceitos | 10 rejeitados (Total: 20 casos)`.

---

### Exemplo de Saída dos Testes Automatizados

Abaixo está o exemplo da saída gerada tanto pelo runner em **C** quanto pelo runner em **Python**:

```text
Compilando o analisador com gcc...
[OK]     .../minic-testes-semanticos/01_promocao_numerica.c
[OK]     .../minic-testes-semanticos/02_sombreamento_lexico.c
[OK]     .../minic-testes-semanticos/03_logica_e_comparacoes.c
[OK]     .../minic-testes-semanticos/04_vetores_e_parametro_array.c
[OK]     .../minic-testes-semanticos/05_lacos_aninhados.c
[OK]     .../minic-testes-semanticos/06_recursao_e_retorno.c
[OK]     .../minic-testes-semanticos/07_void_como_comando.c
[OK]     .../minic-testes-semanticos/08_retornos_nos_dois_ramos.c
[OK]     .../minic-testes-semanticos/09_atribuicao_associativa.c
[OK]     .../minic-testes-semanticos/10_vetor_bool_e_funcoes.c
[OK]     .../minic-testes-semanticos/11_estreitamento_implicito.c
[OK]     .../minic-testes-semanticos/12_identificador_nao_declarado.c
[OK]     .../minic-testes-semanticos/13_declaracao_duplicada.c
[OK]     .../minic-testes-semanticos/14_condicao_nao_booleana.c
[OK]     .../minic-testes-semanticos/15_indice_float.c
[OK]     .../minic-testes-semanticos/16_aridade_incorreta.c
[OK]     .../minic-testes-semanticos/17_tipos_de_argumentos.c
[OK]     .../minic-testes-semanticos/18_uso_de_void_como_valor.c
[OK]     .../minic-testes-semanticos/19_retorno_e_cobertura.c
[OK]     .../minic-testes-semanticos/20_destino_nao_atribuivel.c

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

## Representação Intermediária (IR) — Código de Três Endereços (TAC)

A etapa de Representação Intermediária consome a AST validada e anotada pela análise semântica e produz **Código de Três Endereços (TAC)** explícito e determinístico, mantendo saída textual idêntica nas versões em Python (`ProjetoMiniC/src/ir/`) e C (`C/ir.h`, `C/ir.c`, `C/ir_main.c`). Veja a especificação completa em [`ProjetoMiniC/docs/ir.md`](ProjetoMiniC/docs/ir.md).

### Fluxo e Bloqueio em Caso de Erros

```text
Lexer (2) → Parser/AST (3) → Análise Semântica (4) → Geração de IR (0)
```

Não é gerado IR se houver erro léxico (`2`), sintático (`3`) ou semântico (`4`). Além disso, a API (`generate_ir` em Python e `ir_generate` em C) valida estruturalmente a AST recebida e rejeita árvores vazias, sem anotações semânticas ou com nós `<error>`.

### Como Executar a Geração de IR

```bash
# Em Python:
python3 minic.py --ir arquivo.c
python3 main.py arquivo.c --ir
python3 ir.py arquivo.c
python3 -m ProjetoMiniC.src.ir arquivo.c
python3 -m ProjetoMiniC.src.ir              # abre a interface gráfica (Tkinter) do IR

# Em C (via Makefile ou compilação direta com GCC):
make semantic
./minic --ir arquivo.c

make ir
./ir arquivo.c

# Compilação direta em arquivo único:
gcc -std=c11 -Wall -Wextra -pedantic -O2 minic.c -o minic
./minic --ir arquivo.c

gcc -std=c11 -Wall -Wextra -pedantic -O2 ir.c -o ir
./ir arquivo.c
```

### Formato TAC e Regras de Tradução

- **Declarações e Funções:**
  - Globais: `global <tipo> <nome>` e `global <tipo> <nome>[<tam>]` (com atribuição `<nome> = <val>` quando inicializadas).
  - Funções: `func <tipo_retorno> <nome>:` ... `endfunc` (instruções internas indentadas com 2 espaços).
  - Parâmetros e locais: `param <tipo> <nome_ir>` (incluindo `<tipo>[]`), `local <tipo> <nome_ir>` e `local <tipo> <nome_ir>[<tam>]`.
- **Temporários e Rótulos:**
  - Temporários sequenciais `t1, t2, t3, ...` e rótulos sequenciais `L1, L2, L3, ...`.
- **Expressões, Coerções, Vetores, Chamadas e E/S:**
  - Binárias: `t1 = a + b`, `t2 = x < 10`, `t3 = p && q`.
  - Unárias: `t1 = - x`, `t2 = ! ok`.
  - Promoção numérica `int → float` (`coercion_type` e `chain_coercion_type`): `t1 = int2float n`.
  - Vetores: leitura `t1 = v[i]` e escrita `v[i] = val`.
  - Chamadas e retornos: `arg <val>` para cada argumento, `t1 = call f, <n>` (ou `call f, <n>` para retorno `void`), `return <val>` ou `return`.
  - Entrada e saída: `read x`, `read v[i]` e `print val`.
- **Escopos e Desambiguação de Identificadores:**
  - Utiliza os símbolos e números de escopo resolvidos pela análise semântica. Variáveis locais ou parâmetros que sombreiam variáveis globais ou declarações anteriores na mesma função recebem o sufixo determinístico `$<escopo>` (por exemplo, `x$1`, `x$2`), evitando colisões de nomes.
- **Controle de Fluxo e Laços Aninhados:**
  - `if`/`else`, `while` e `for` são convertidos em `if_false <cond> goto L<n>`, `goto L<n>` e rótulos `L<n>:`.
  - Uma pilha de alvos de laço `(continue_label, break_label)` garante que `break` e `continue` em laços aninhados desviem sempre para o laço imediatamente envolvente (no `for`, `continue` salta para o rótulo de incremento `L_step` antes de reavaliar a condição).

### Testes de IR

```bash
python -m unittest discover -s tests -p test_ir.py -v
make test-ir
```


