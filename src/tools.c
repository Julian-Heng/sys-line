#if defined(__linux__)
#   define _DEFAULT_SOURCE
#endif

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

#include "tools.h"
#include "macros.h"

bool find(char* const base, char* const pattern, char* str, int size)
{
    char buf[BUFSIZ];
    bool found = false;
    bool end = false;

    FTS* ftsp = NULL;
    FTSENT* entry = NULL;

    regex_t re;

    if ((ftsp = fts_open(&base, FTS_PHYSICAL, NULL)) &&
        ! regcomp(&re, pattern, REG_EXTENDED))
    {
        while (! found && ! end)
            if (!(entry = fts_read(ftsp)))
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

        regfree(&re);
    }

    if (ftsp)
        fts_close(ftsp);

    return found;
}


char** find_all(char* const base, char* const pattern, int maxsize, int* count)
{
    bool end = false;
    char** paths = NULL;
    int i;

    *count = 0;

    FTS* ftsp = NULL;
    FTSENT* entry = NULL;

    regex_t re;

    if ((ftsp = fts_open(&base, FTS_PHYSICAL, NULL)) &&
        ! regcomp(&re, pattern, REG_EXTENDED))
    {
        paths = (char**)malloc(maxsize * sizeof(char*));
        for (i = 0; i < maxsize; i++)
            paths[i] = NULL;

        while (! end && *count < maxsize)
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

        regfree(&re);
    }

    if (ftsp)
        fts_close(ftsp);

    return paths;
}


void __free(void** p)
{
    if (*p)
    {
        free(*p);
        *p = NULL;
    }
}
