# Projeto MiniC

Compilador educacional para a linguagem **MiniC**, um subconjunto de C. O projeto possui implementacoes equivalentes em Python e C para o analisador lexico e o analisador sintatico, uma interface grafica em Tkinter, ferramentas de linha de comando e suites de testes para as duas implementacoes.

O objetivo do projeto e construir gradualmente um pipeline de compilacao: leitura do codigo-fonte, analise lexica, analise sintatica, construcao da AST, analise semantica, geracao de representacao intermediaria, otimizacao e geracao de codigo.

## Estado atual

| Etapa | Python | C |
|---|---|---|
| Analise lexica | Implementada | Implementada |

O scanner C escreve tokens JSONL em `stdout` e erros JSONL em `stderr`. Os modulos C principais sao:

- `C/scanner.c` e `C/scanner.h`: varredura do texto-fonte.
- `C/token.c` e `C/token.h`: estrutura dos tokens.
- `C/token_types.c` e `C/token_types.h`: tipos e palavras reservadas.
- `C/errors.c` e `C/errors.h`: erros lexicos.
- `C/util.c` e `C/util.h`: memoria, strings dinamicas e leitura de arquivos.
- `C/main.c`: CLI e serializacao JSONL do scanner.
- `C/parser.c`, `C/parser_main.c`: parser e entrada CLI do parser.
- `C/ast.c` e `C/ast.h`: nos e serializacao da AST.

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
| 0 | Analise concluida com sucesso |
| 1 | Uso incorreto ou erro de leitura |
| 2 | Erro lexico |
| 3 | Erro sintatico |

Os parsers Python e C seguem esse contrato para a CLI. A interface grafica apresenta os mesmos resultados em suas abas de AST, arvore, diagnosticos e tokens.

## Documentacao tecnica

- `ProjetoMiniC/docs/README.md`: detalhes da implementacao Python.
- `ProjetoMiniC/docs/gramatica.ebnf`: arquivo reservado para a gramatica EBNF completa; a gramatica usada pelo parser esta implementada em `src/parser/parser.py` e em `C/parser.c`.
- `ProjetoMiniC/docs/especificacao.md`: especificacao lexica executavel, regras de tokens, recuperacao e formato JSONL.
- `ProjetoMiniC/docs/arquitetura.md`: documento reservado para a arquitetura geral do compilador.
- `testes-parser-50/README.md`: formato e regras do pacote externo.
- `testes-parser-50/EXECUCAO.txt`: comandos minimos por caso.

## Limitacoes atuais

- A analise semantica esta implementada em Python e C e passou nos 20 casos
  fornecidos em ambas as linguagens, com diagnosticos identicos aos gabaritos.
  Veja [documentacao semantica](ProjetoMiniC/docs/semantica.md).
- Os pacotes de IR, otimizacao e geracao de codigo ainda sao estruturas de organizacao.
- A interface grafica oferece atalhos para essas etapas, mas informa que estao em desenvolvimento.
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
- **Parser em C:** rejeita os 25 casos inválidos, mas só 3 dos 25 casos válidos batem com a AST esperada, porque a saída em C ainda usa o formato antigo (por exemplo `VarDecl(int x,Lit(42))` em vez do formato do Python). Por isso, `make test-parser`, que compara a saída de Python e C, ainda falha até o formato ser alinhado.

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

## Análise semântica

```bash
python3 minic.py arquivo.c
python3 main.py arquivo.c --semantic
make semantic
./minic arquivo.c
make test-semantic
```

Os wrappers `minic.py` e `minic.c` executam lexer → parser/AST → semântica,
preservando `parser.py` e `parser.c` como entradas sintáticas. Erros semânticos
retornam 4. Regras, contrato de diagnósticos e resultados de validação estão em
[semantica.md](ProjetoMiniC/docs/semantica.md).

Suíte semântica fornecida (20/20 em cada linguagem):

```bash
bash testes_semanticos_py.sh minic.py minic-testes-semanticos
bash testes_semanticos_c.sh minic.c minic-testes-semanticos
```
