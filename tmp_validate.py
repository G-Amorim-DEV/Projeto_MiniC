from ProjetoMiniC.src.lexer.scanner import Scanner

source = 'int main() { return 0; }'
scanner = Scanner(source)
tokens = scanner.scan_tokens()
print([(t.type.name, t.lexeme, t.line, t.column) for t in tokens[:8]])
print('errors', scanner.errors)
