# Comandos do projeto

CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -pedantic -O2
SRC = C/main.c C/scanner.c C/token.c C/token_types.c C/errors.c C/util.c
OBJ = $(SRC:.c=.o)
TARGET = C/minic_scanner

# Compatibilidade para comando de remoção no Windows e Linux
ifeq ($(OS),Windows_NT)
    RM = del /Q /F
    EXT = .exe
else
    RM = rm -f
    EXT =
endif

TARGET_BIN = $(TARGET)$(EXT)

all: $(TARGET_BIN)

$(TARGET_BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Executa o scanner sobre todos os programas válidos de teste
test-valid: $(TARGET_BIN)
	@echo "=== Rodando Testes Validos (Programas C) ==="
	@for file in ProjetoMiniC/casos-programas-c/*.c; do \
		echo "Analisando $$file..."; \
		./$(TARGET_BIN) --jsonl "$$file" > "$$file.c.out.jsonl" 2>/dev/null; \
	done

# Executa o scanner sobre os casos invalidos
test-invalid: $(TARGET_BIN)
	@echo "=== Rodando Testes Invalidos ==="
	@for file in ProjetoMiniC/casos-invalidos/*.minic; do \
		echo "Analisando $$file..."; \
		./$(TARGET_BIN) --jsonl "$$file" > "$$file.out.jsonl" 2> "$$file.err.jsonl" || true; \
	done

# Roda ambos os testes
test: test-valid test-invalid

clean:
	$(RM) C/*.o $(TARGET_BIN)
	$(RM) ProjetoMiniC/casos-programas-c/*.out.jsonl
	$(RM) ProjetoMiniC/casos-invalidos/*.out.jsonl
	$(RM) ProjetoMiniC/casos-invalidos/*.err.jsonl

.PHONY: all clean test test-valid test-invalid
