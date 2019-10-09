#if defined(__linux__)
#   define _DEFAULT_SOURCE
#endif

#include <ctype.h>
#include <errno.h>
#include <fts.h>
#include <regex.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <sys/stat.h>
#include <sys/types.h>

#include "macros.h"
#include "tools.h"


bool find(char* base, char* pattern, char* str, int size)
{
    bool found = false;
    bool end = false;

    FTS* ftsp = NULL;
    FTSENT* entry = NULL;

    char* fts_paths[] = {base, NULL};

    regex_t re;

    if ((ftsp = fts_open(fts_paths, FTS_PHYSICAL, NULL)) &&
        ! regcomp(&re, pattern, REG_EXTENDED))
    {
        while (! found && ! end)
        {
            if (! (entry = fts_read(ftsp)))
            {
                if (errno == 0)
                    end = true;
                else
                {
                    perror("fts_read");
                    exit(EXIT_FAILURE);
                }
            }
            else if ((entry->fts_info & FTS_F || entry->fts_info & FTS_DP) &&
                     ! regexec(&re, entry->fts_path, 0, NULL, 0))
            {
                strncpy(str, entry->fts_path, size);
                found = true;
            }
        }

        regfree(&re);
    }

    if (ftsp)
        fts_close(ftsp);

    return found;
}


char** find_all(char* base, char* pattern, int maxsize, int* count)
{
    bool end = false;
    char** paths = NULL;
    int i;

    *count = 0;

    FTS* ftsp = NULL;
    FTSENT* entry = NULL;

    char* fts_paths[] = {base, NULL};

    regex_t re;

    if ((ftsp = fts_open(fts_paths, FTS_PHYSICAL, NULL)) &&
        ! regcomp(&re, pattern, REG_EXTENDED))
    {
        paths = (char**)malloc(maxsize * sizeof(char*));
        for (i = 0; i < maxsize; i++)
            paths[i] = NULL;

        while (! end && *count < maxsize)
        {
            if (!(entry = fts_read(ftsp)))
            {
                if (errno == 0)
                    end = true;
                else
                {
                    perror("fts_read");

                    for (i = 0; i < maxsize; i++)
                        _free(paths[i]);
                    _free(paths);

                    exit(EXIT_FAILURE);
                }
            }
            else if ((entry->fts_info & FTS_F || entry->fts_info & FTS_DP) &&
                     ! regexec(&re, entry->fts_path, 0, NULL, 0))
            {
                paths[*count] = (char*)malloc(maxsize * sizeof(char));
                strncpy(paths[(*count)++], entry->fts_path, maxsize);
            }
        }

        regfree(&re);
    }

    if (ftsp)
        fts_close(ftsp);

    return paths;
}


void trim(char* str)
{
    int i, x;
    for (i = x = 0; str[i]; ++i)
        if (! isspace(str[i]) || (i > 0 && ! isspace(str[i - 1])))
            str[x++] = str[i];
    str[x] = '\0';
}
