# Projeto MiniC

Este repositório reúne uma implementação do compilador MiniC em duas linguagens:

- Python
- C

O objetivo do projeto é desenvolver uma ferramenta para análise de código em linguagem C, cobrindo etapas fundamentais de compilação, como:

- identificação de tokens
- análise léxica
- análise sintática
- análise semântica

## Visão geral

O projeto está organizado em subpastas por linguagem e por módulos do compilador. A parte em Python já contém a estrutura base do lexer, além de uma interface em Tkinter para testar a análise léxica com diferentes entradas.

## Estrutura do repositório

```text
Projeto_MiniC/
├── README.md
├── ProjetoMiniC/
│   ├── Python/
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── lexer/
│   │   │   │   ├── __main__.py
│   │   │   │   ├── demo.py
│   │   │   │   ├── scanner.py
│   │   │   │   ├── token_types.py
│   │   │   │   ├── tokens.py
│   │   │   │   └── errors.py
│   │   │   ├── parser/
│   │   │   ├── semantic/
│   │   │   ├── ast/
│   │   │   ├── codegen/
│   │   │   ├── ir/
│   │   │   └── optimizer/
│   │   └── docs/
│   └── C/
```

## Executando a versão em Python

Acesse a pasta do projeto Python:

```powershell
cd "C:\Users\guilherme.lima\OneDrive - Alpargatas S.A\Documentos\GitHub\Projeto_MiniC\ProjetoMiniC\Python"
```

Se o ambiente ainda não tiver o Python configurado, use o `uv` para instalar uma versão funcional:

```powershell
uv python install 3.12
```

Depois execute o analisador léxico com a interface gráfica:

```powershell
uv run python -m src.lexer
```

## Interface de uso

A entrada principal em `src.lexer` agora oferece uma interface em Tkinter com três opções:

1. executar os testes embutidos do lexer;
2. colar um trecho de código na própria interface e analisar;
3. abrir um arquivo `.py` para realizar a análise léxica.

A saída mostra os tokens reconhecidos e os erros léxicos encontrados, mantendo o fluxo de depuração do compilador.

## O que o lexer faz

O módulo de lexer está responsável por:

- percorrer o código-fonte caractere por caractere
- reconhecer palavras reservadas, identificadores, números e operadores
- identificar strings, caracteres e comentários
- registrar erros léxicos como símbolos inválidos, strings não fechadas e comentários sem fechamento
- produzir a lista de tokens para etapas posteriores do compilador

## Observações

- O projeto ainda está em evolução e os módulos posteriores (parser, semântica e geração de código) continuam sendo estruturados.
- A parte em Python é a base mais avançada no momento e funciona como referência para os demais módulos.
- A interface gráfica facilita os testes de entrada e diagnóstico em um fluxo visual e prático.

## Análise sintática — Etapa 2

O parser consome diretamente os `Token` produzidos pelo lexer e constrói uma
AST tipada para declarações, funções, comandos e expressões. A saída de linha
de comando é uma S-expression, por exemplo
`Program(Function(int main() Block(Return(Lit(0)))))`.

```bash
# Python (somente biblioteca padrão)
python3 parser.py codigo.c

# C (compila o parser sem substituir o scanner da Etapa 1)
make parser
./parser codigo.c

# Regressão do parser (executa as mesmas entradas em Python e C)
make test-parser
```

Na interface principal (`python3 main.py`), o botão **Análise Sintática** abre
uma tela própria para digitar ou carregar um arquivo, executar o parser e
consultar a AST, os diagnósticos com linha/coluna e os tokens reconhecidos.

Os códigos de saída são: `0` para sucesso, `1` para uso/leitura inválidos,
`2` para erro léxico e `3` para erro sintático. A versão C usa apenas a
biblioteca padrão de C e a versão Python usa apenas a biblioteca padrão; o
`tkinter` é usado somente pelas interfaces gráficas dos analisadores léxico e
sintático.

Os testes de regressão cobrem declarações globais e locais (inclusive listas
separadas por vírgula), vetores, funções, parâmetros, controle de fluxo,
entrada/saída, chamadas, indexação, precedência e associatividade. Além de
aceitar ou rejeitar cada caso, eles verificam que as duas implementações
produzem exatamente a mesma representação textual da AST.

## Tecnologias

- Python
- Tkinter
- uv (gerenciamento de ambiente Python)
- Git / GitHub para versionamento
