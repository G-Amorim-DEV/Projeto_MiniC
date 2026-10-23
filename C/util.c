#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "util.h"

void *xmalloc(size_t size) {
    void *p = malloc(size);
    if (!p) {
        fprintf(stderr, "Erro fatal: memoria insuficiente.\n");
        exit(EXIT_FAILURE);
    }
    return p;
}

void *xrealloc(void *ptr, size_t size) {
    void *p = realloc(ptr, size);
    if (!p) {
        fprintf(stderr, "Erro fatal: memoria insuficiente.\n");
        exit(EXIT_FAILURE);
    }
    return p;
}

char *xstrdup(const char *s) {
    if (!s) return NULL;
    size_t len = strlen(s) + 1;
    char *copy = (char *)xmalloc(len);
    memcpy(copy, s, len);
    return copy;
}

void dynstr_init(DynStr *s) {
    s->cap = 16;
    s->len = 0;
    s->data = (char *)xmalloc(s->cap);
    s->data[0] = '\0';
}

void dynstr_push_char(DynStr *s, char c) {
    if (s->len + 1 >= s->cap) {
        s->cap *= 2;
        s->data = (char *)xrealloc(s->data, s->cap);
    }
    s->data[s->len++] = c;
    s->data[s->len] = '\0';
}

void dynstr_push_str(DynStr *s, const char *str) {
    if (!str) return;
    while (*str) {
        dynstr_push_char(s, *str++);
    }
}

void dynstr_free(DynStr *s) {
    if (s->data) {
        free(s->data);
        s->data = NULL;
    }
    s->len = 0;
    s->cap = 0;
}

char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) {
        return NULL;
    }

    fseek(f, 0, SEEK_END);
    long length = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (length < 0) {
        fclose(f);
        return NULL;
    }

    char *buffer = (char *)xmalloc(length + 1);
    size_t read_bytes = fread(buffer, 1, length, f);
    buffer[read_bytes] = '\0';
    size_t j = 0;
    for (size_t i = 0; i < read_bytes; i++) {
        if (buffer[i] == '\r' && (i + 1 < read_bytes) && buffer[i + 1] == '\n') {
            continue;
        }
        buffer[j++] = buffer[i];
    }
    buffer[j] = '\0';

    fclose(f);
    return buffer;
}