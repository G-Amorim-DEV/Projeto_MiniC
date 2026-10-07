# Análise semântica Python e C

A etapa consome a AST construída pelos parsers existentes. Não há um segundo
parser no analisador semântico. `parser.py`, `parser.c`, `--parse`, `--ast` e as
interfaces gráficas mantêm seu contrato de análise sintática e serialização.

## Execução na raiz do repositório

```bash
python3 minic.py arquivo.c
python3 main.py arquivo.c --semantic
make semantic
./minic arquivo.c
# Alternativa esperada por runners que compilam um único arquivo:
gcc -std=c11 -Wall -Wextra -pedantic -O2 minic.c -o /tmp/minic
/tmp/minic arquivo.c
make test-semantic
```

Os wrappers `minic.py` e `minic.c` permitem manter os pontos de entrada sintáticos
existentes. Runners semânticos devem apontar para esses wrappers. Códigos de
saída: 0 sucesso, 1 uso/leitura, 2 erro léxico, 3 erro sintático, 4 erro semântico.
Diagnósticos semânticos e resumo vão para stdout; uso, leitura e erros das etapas
anteriores vão para stderr. A CLI semântica não imprime tokens nem AST.

## Regras implementadas

- Símbolos com nome, tipo, categoria, escopo e posição; escopos léxicos de
  função/bloco; sombreamento interno e rejeição de duplicatas locais.
- Assinaturas de todas as funções registradas antes da análise dos corpos;
  recursão e chamadas a funções definidas depois são permitidas.
- Tipagem de literais, identificadores, chamadas, índices, atribuições,
  operadores e retornos; promoção escalar int → float, sem estreitamento
  implícito float → int. Vetores exigem compatibilidade exata do tipo base.
- Aritmética numérica, módulo inteiro, relações numéricas, igualdade numérica,
  booleana ou de caracteres e lógica booleana. Condições if/while/for são bool.
- Índices e tamanhos de vetor são int; acesso exige vetor; argumentos array
  são vetores, sem promoção elemento a elemento.
- Chamadas validam existência, categoria, aridade e tipos. Void é permitido
  como comando, mas não como valor.
- Atribuição/read exigem variável escalar ou elemento de vetor atribuível;
  atribuição a vetor completo é rejeitada. Atribuições são comandos sem valor;
  seu uso em argumentos, retornos, operadores ou condições é rejeitado.
- Retornos compatíveis com a função. Cobertura considera sequências e ambos
  os ramos de if/else; if sem else e laços não garantem retorno.
- Break/continue exigem laço. Não é exigida função main/principal.

No modo semântico o parser permite uma AST de atribuição com destino inválido,
para que a regra de atribuibilidade seja verificada nesta etapa. No modo
sintático padrão continua rejeitando esse destino, preservando as regressões.

## Metadados da AST

Nós conservam linha/coluna a partir de 1 e texto de tokens para diagnósticos.
Metadados não entram na S-expression. As posições de declarações são as dos
identificadores; expressões usam o início da expressão. O texto conserva a
grafia dos literais e normaliza espaços entre tokens; não usa S-expression.
Parâmetros C ficam em metadados próprios do nó Function, produzidos durante a
análise dos parâmetros, sem mudar os filhos serializados da AST.

## Contrato de diagnósticos e validação

Os scripts e a pasta `minic-testes-semanticos` fornecidos foram incorporados
sem alterar seus conteúdos. O contrato está em
`minic-testes-semanticos/GABARITO.md`: SEM001/002/003/005/006/007/008/009/011/012/013,
mensagens canônicas, posições 1-based, ordem de origem e resumo de aceitação
ou rejeição. A CLI usa CRLF entre linhas e não acrescenta quebra depois do resumo,
reproduzindo os bytes dos `.gabarito` recebidos. O catálogo cobre os casos
fornecidos; erros adicionais de operadores, categoria de chamada/vetor e controle
usam códigos `E_OPERATOR`, `E_CALL`, `E_ARRAY`, `E_FUNCTION_VALUE` e
`SEM010` para contexto, conforme a Aula 15; os códigos `E_*` restantes
representam casos adicionais sem texto canônico fornecido no pacote.

```bash
bash testes_semanticos_py.sh minic.py minic-testes-semanticos
bash testes_semanticos_c.sh minic.c minic-testes-semanticos
bash testar_parser_python.sh testes-parser-50 parser.py
bash testar_parser_c.sh testes-parser-50 parser.c
python3 -m unittest discover -s tests -v
python3 -m ProjetoMiniC.src.lexer.fixture_runner ProjetoMiniC
```

Resultados:

- 20/20 casos semânticos fornecidos em Python, zero falhas.
- 20/20 em C, zero falhas; os bytes das saídas Python/C e os códigos de saída
  também são comparados diretamente em `tests/test_semantic.py`.
- 53 casos semânticos adicionais: 16 aceitos e 37 rejeitados, com paridade
  Python/C, além de testes de posições, texto original, símbolos, reuso e CLI.
- 50/50 casos sintáticos do professor em cada linguagem.
- 14 métodos unittest passaram, incluindo regressões do parser e interface.
- 10/10 fixtures léxicas disponíveis passaram em Python; a entrada de
  `i06_identificador_iniciado_por_digito` continua ausente e não foi inventada.
- C compilado com `-std=c11 -Wall -Wextra -pedantic -Werror -O2`.

Conflitos e correções de regressão: duas expectativas antigas em
`tests/test_parser.py` usavam `Lit(1)`/`Lit(0)`, enquanto as ASTs e os gabaritos
sintáticos oficiais usam `Lit(int,1)`/`Lit(int,0)`. As expectativas foram alinhadas
à referência oficial, mantendo comparações literais da AST completa. O formato
público da AST foi preservado. Corrigidas a chamada inexistente `diagnostic()`
por compatibilidade com `diagnostico()`, as aspas adicionais de string/char na
AST C e a recuperação Python de literais não terminados, alinhada aos fixtures
e ao scanner C. Os gabaritos não foram alterados.

## Conferência com a Aula 15

Foi lida a apostila **Aula 15: Conclusão da análise semântica**, do professor
Alex Torquato Souza Carneiro, fornecida como `Aula15 - Compiladores.pdf`.
O verificador foi ajustado em Python e C após a conferência:

| Páginas/slides | Regra | Implementação e evidência |
|---|---|---|
| 3, 5–7, 19 | AST anotada, usos resolvidos e coerções | Cada expressão mantém `semantic_type`; usos referenciam símbolos/declarações; int→float é registrado em `coercion_type`, sem gerar IR. |
| 5–6, 16–17 | ERROR suprime erros derivados | Erros primários propagam `<error>` aos pais; testes de índice, chamada e atribuição inválidos confirmam um diagnóstico primário e preservação de erros independentes. |
| 7–10 | Uma regra de compatibilidade | Inicializadores, atribuições, argumentos, retornos e promoções usam a mesma compatibilidade int→float; bool não participa da aritmética. |
| 8 | Atribuição é comando sem valor | Uso de atribuição como valor é rejeitado com SEM003; cadeias usadas como comando permanecem permitidas conforme explicado abaixo. |
| 4, 11 | Tipo de índice ≠ limites em execução | Vetores conservam dimensão e tipo de elemento; índice exige int. Não se rejeita um índice int apenas por seu valor ser fora dos limites. |
| 12–15 | Assinaturas, retornos e contexto | Assinaturas são coletadas antes dos corpos; fluxo conservador; break/continue/return respeitam contexto. |
| 16 | SEM010 para contexto | Break e continue fora de laço e return fora de função usam SEM010. |
| 18 | Exemplo completo da aula | O programa soma/promove/principal integra os testes positivos e passa em ambas as linguagens. |

As anotações Python incluem `resolved_symbol` (tipo, categoria, escopo,
posição, declaração e dimensão). Em C, `resolved_declaration` aponta para um nó
persistente da AST, que conserva tipo, categoria, escopo e dimensão; não aponta
para a tabela temporária já liberada. A vida dessas referências é a da AST.
As S-expressions e a igualdade dos nós Python continuam preservadas.
Testes verificam as anotações das duas linguagens, todas as coerções exigidas,
reuso da mesma AST e sua serialização antes/depois da análise.

**Diferença com o gabarito 09:** o texto do pacote descreve `a = b = 3` como
recebimento do resultado da atribuição, enquanto o slide 8 define atribuição como
comando sem valor. A implementação segue a aula: uma cadeia em posição de
comando é uma sequência de gravações da direita para a esquerda. O tipo do
destino já gravado é usado para validar a próxima gravação; nenhum nó Assign
sintetiza valor-R. Todos os nós da cadeia são anotados como void (ou ERROR).
Uma promoção entre gravações fica em `chain_coercion_type`, distinta de uma
coerção de valor-R. Assim o caso 09 continua aceito sem permitir `return (a=1)`,
`f(a=1)` ou `if (a=1)`. A diferença é explícita e coberta por testes.

O slide 12 menciona concordância entre protótipos e definições. A gramática
existente só admite definições com corpo, e o teste sintático oficial 48 rejeita
uma declaração de função sem corpo. Não foi introduzida sintaxe de protótipos;
as assinaturas verificadas são coletadas das definições aceitas pelo parser.
Não há alteração dos gabaritos para conciliar essa limitação da gramática.
A interface Tkinter foi validada por sua função de análise e testes existentes;
não houve validação visual em sessão gráfica.
