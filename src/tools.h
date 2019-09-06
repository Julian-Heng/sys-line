#ifndef TOOLS_H
#define TOOLS_H

void __free(void**);
bool find(char*, char*, char*, int);
char** find_all(char*, char* , int, int*);
void re_replace(char*, char*, char*, int);
void re_replace_all(char*, char*, char*, int);
static void __replace(regex_t, char*, char*, int);
void trim(char*);

#endif
