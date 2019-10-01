#if defined(__linux__)

#include <regex.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"
#include "../commons/swap.h"

#include "swap.h"


bool __get_swap_used(struct swap_info* swap)
{
    bool ret = false;
    long long free = 0;

    FILE* fp = NULL;

    bool cond = false;
    char buf[BUFSIZ];
    char tmp[BUFSIZ];

    regex_t re;
    regmatch_t group[2];

    if (! swap->total)
        __get_swap_total(swap);

    if ((ret = (fp = fopen("/proc/meminfo", "r"))) &&
        ! regcomp(&re, USED_REG, REG_EXTENDED))
    {
        memset(buf, 0, BUFSIZ);
        memset(tmp, 0, BUFSIZ);

        while (! cond && fgets(buf, BUFSIZ, fp))
            if ((cond = ! regexec(&re, buf, 2, group, 0)))
                strncpy(tmp, buf + group[1].rm_so,
                        group[1].rm_eo - group[1].rm_so);

        free = atoll(tmp) << 10;
        regfree(&re);
    }

    _fclose(fp);

    if (ret)
        swap->used = swap->total - free;

    return ret;
}


bool __get_swap_total(struct swap_info* swap)
{
    bool ret = false;
    long long total = 0;

    FILE* fp = NULL;

    bool cond = false;
    char buf[BUFSIZ];
    char tmp[BUFSIZ];

    regex_t re;
    regmatch_t group[2];

    if ((ret = (fp = fopen("/proc/meminfo", "r"))) &&
        ! regcomp(&re, TOTAL_REG, REG_EXTENDED))
    {
        memset(buf, 0, BUFSIZ);
        memset(tmp, 0, BUFSIZ);

        while (! cond && fgets(buf, BUFSIZ, fp))
            if ((cond = ! regexec(&re, buf, 2, group, 0)))
                strncpy(tmp, buf + group[1].rm_so,
                        group[1].rm_eo - group[1].rm_so);

        total = atoll(tmp) << 10;
        regfree(&re);
    }

    _fclose(fp);

    if (ret)
        swap->total = total;

    return ret;
}

#endif
