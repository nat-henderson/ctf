#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main() {
    char* str_pointer = NULL;
    size_t i = 0;
    getline(&str_pointer, &i, stdin);
    char cmd[120];
    strcpy(cmd, "ls ");
    strcat(cmd, str_pointer);
    FILE* output;
    output = popen(cmd, "w");
    fflush(stdout);
    printf("\n");
    fflush(stdout);
    exit(0);
}
