"""
errors.py
=========
Classes de erro especializadas para captura e tratamento de problemas durante a análise léxica.
"""


class ErroLexico(Exception):
    """Classe base para qualquer inconsistência léxica identificada no código."""
    codigo: str = "ERRO_LEXICO"

    def __init__(self, mensagem: str, linha: int, coluna: int, lexema: str = ""):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.lexema = lexema
        self.codigo = self.__class__.codigo
        super().__init__(self.diagnostico())

    def diagnostico(self) -> str:
        """Gera mensagem formatada indicando a posição exata e contexto do erro."""
        origem = f" próximo de {self.lexema!r}" if self.lexema else ""
        return f"linha {self.linha}, coluna {self.coluna}: {self.mensagem}{origem}"

    def diagnostic(self) -> str:
        return self.diagnostico()


class ErroSimboloInvalido(ErroLexico):
    codigo = "UNKNOWN_SYMBOL"

    def __init__(self, caractere: str, linha: int, coluna: int):
        super().__init__(
            f"símbolo inválido '{caractere}' (caractere não reconhecido pela gramática)",
            linha,
            coluna,
            caractere,
        )


class ErroIdentificadorInvalido(ErroLexico):
    codigo = "IDENTIFICADOR_INVALIDO"

    def __init__(self, lexema: str, linha: int, coluna: int):
        super().__init__(
            "identificador inválido (não é permitido iniciar identificadores com dígitos)",
            linha,
            coluna,
            lexema,
        )


class ErroLiteralRealMalformado(ErroLexico):
    codigo = "MALFORMED_REAL_LITERAL"

    def __init__(self, lexema: str, linha: int, coluna: int):
        super().__init__(
            "literal real malformado (esperada parte decimal após o ponto '.')",
            linha,
            coluna,
            lexema,
        )


class ErroCadeiaNaoTerminada(ErroLexico):
    codigo = "UNTERMINATED_STRING_LITERAL"

    def __init__(self, trecho_parcial: str, linha: int, coluna: int):
        super().__init__(
            "cadeia de caracteres não terminada (ausência de aspas duplas de fechamento)",
            linha,
            coluna,
            trecho_parcial,
        )


class ErroComentarioNaoTerminado(ErroLexico):
    codigo = "UNTERMINATED_BLOCK_COMMENT"

    def __init__(self, linha: int, coluna: int, lexema: str = ""):
        super().__init__(
            "comentário de bloco não terminado (ausência do delimitador de fechamento '*/')",
            linha,
            coluna,
            lexema,
        )


class ErroCaractereNaoTerminado(ErroLexico):
    codigo = "UNTERMINATED_CHAR_LITERAL"

    def __init__(self, trecho_parcial: str, linha: int, coluna: int):
        super().__init__(
            "literal de caractere malformado (ausência de aspas simples ' de fechamento)",
            linha,
            coluna,
            trecho_parcial,
        )
