#ifndef TOOLS_H
#define TOOLS_H

#include <stdbool.h>

bool find(char*, char*, char*, int);
char** find_all(char*, char* , int, int*);
void re_replace(char*, char*, char*, int);
void re_replace_all(char*, char*, char*, int);
void trim(char*);

#endif
