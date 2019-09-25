#if defined(__linux__)

#include <regex.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"
#include "../../utils/tools.h"
#include "../commons/mem.h"

#include "mem.h"


bool __get_mem_used(struct mem_info* mem)
{
    bool ret = false;
    long long used = 0;

    FILE* fp;

    char buf[BUFSIZ];
    char tmp[BUFSIZ];

    regex_t re_used;
    regex_t re_free;
    regmatch_t group[3];

    if ((ret = (fp = fopen("/proc/meminfo", "r")) &&
        ! regcomp(&re_used, USED_TOTAL_REG, REG_EXTENDED) &&
        ! regcomp(&re_free, USED_FREE_REG, REG_EXTENDED)))
    {
        memset(buf, 0, BUFSIZ);
        memset(tmp, 0, BUFSIZ);

        while (fgets(buf, BUFSIZ, fp))
        {
            if (! regexec(&re_used, buf, 3, group, 0))
            {
                memset(tmp, 0, BUFSIZ);
                strncpy(tmp, buf + group[2].rm_so,
                        group[2].rm_eo - group[2].rm_so);
                used += atoll(tmp) << 10;
            }
            else if (! regexec(&re_free, buf, 3, group, 0))
            {
                memset(tmp, 0, BUFSIZ);
                strncpy(tmp, buf + group[2].rm_so,
                        group[2].rm_eo - group[2].rm_so);
                used -= atoll(tmp) << 10;
            }
        }
    }

    _fclose(fp);
    regfree(&re_used);
    regfree(&re_free);

    if (ret)
        mem->used = used;

    return ret;
}


bool __get_mem_total(struct mem_info* mem)
{
    bool ret = false;
    long long total = 0;

    FILE* fp;

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
        mem->total = total;

    return ret;
}

#endif
