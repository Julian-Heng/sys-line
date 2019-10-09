#include <regex.h>
#include <stdlib.h>
#include <string.h>

#include "macros.h"
#include "regtools.h"


static void __replace(regex_t, char*, char*, int);

void re_replace(char* regex, char* sub, char* dest, int size)
{
    regex_t re;

    if (! regcomp(&re, regex, REG_EXTENDED))
    {
        __replace(re, sub, dest, size);
        regfree(&re);
    }
}


void re_replace_all(char* regex, char* sub, char* dest, int size)
{
    char* old = NULL;
    regex_t re;

    if (! regcomp(&re, regex, REG_EXTENDED))
    {
        old = (char*)malloc(size * sizeof(char));

        do
        {
            strncpy(old, dest, size);
            __replace(re, sub, dest, size);
        } while (strncmp(old, dest, size));

        regfree(&re);
        _free(old);
    }
}


static void __replace(regex_t re, char* sub, char* dest, int size)
{
    char* cpy = NULL;

    int str_len = strlen(dest);
    int sub_len = strlen(sub);

    regmatch_t group[1];

    cpy = (char*)malloc(size * sizeof(char));
    strncpy(cpy, dest, size);

    if (! regexec(&re, dest, 1, group, 0) &&
        (str_len + sub_len - (group[0].rm_eo - group[0].rm_so)) < size)
    {
        memset(dest, 0, size);
        strncpy(dest, cpy, group[0].rm_so);
        strncpy(dest + group[0].rm_so, sub, sub_len);
        strncpy(dest + (group[0].rm_so + sub_len), cpy + group[0].rm_eo,
                str_len - group[0].rm_eo);
    }

    _free(cpy);
}
