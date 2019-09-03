#if defined(__linux__)
#   define _DEFAULT_SOURCE
#endif

#include <errno.h>
#include <fts.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <sys/stat.h>
#include <sys/types.h>

#include "tools.h"


bool find(char* const base, char* const file, char* str, int size)
{
    bool found = false;
    bool end = false;

    FTS* ftsp;
    FTSENT* entry;

    if ((ftsp = fts_open(&base, FTS_PHYSICAL, NULL)))
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
            else if (entry->fts_info & FTS_F &&
                     ! strcmp(entry->fts_name, file))
            {
                strncpy(str, entry->fts_path, size);
                found = true;
            }

        fts_close(ftsp);
    }

    return found;
}
