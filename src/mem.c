#if defined(__linux__)
#   include <regex.h>
#   define TOTAL_REG "^MemTotal:\\s+([0-9]+)"
#   define USED_TOTAL_REG "^(MemTotal|Shmem):\\s+([0-9]+)"
#   define USED_FREE_REG "^(MemFree|Buffers|Cached|SReclaimable):\\s+([0-9]+)"
#endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mem.h"
#include "macros.h"

struct mem_info* init_mem()
{
    struct mem_info* mem;

    if ((mem = (struct mem_info*)malloc(sizeof(struct mem_info))))
        memset(mem, 0, sizeof(struct mem_info));

    return mem;
}


bool get_mem_used(struct mem_info* mem)
{
    bool ret = false;

    int used = 0;
#if defined(__linux__)
    FILE* fp;

    char buf[BUFSIZ];
    char tmp[BUFSIZ];

    regex_t re_used;
    regex_t re_free;
    regmatch_t group[3];

    if ((ret = (fp = fopen("/proc/meminfo", "r"))) &&
        ! regcomp(&re_used, USED_TOTAL_REG, REG_EXTENDED) &&
        ! regcomp(&re_free, USED_FREE_REG, REG_EXTENDED))
    {
        memset(buf, 0, BUFSIZ);
        memset(tmp, 0, BUFSIZ);

        while (fgets(buf, BUFSIZ, fp))
        {
            if (! regexec(&re_used, buf, 3, group, 0))
            {
                memset(tmp, 0, BUFSIZ);
                strncpy(tmp, buf + group[2].rm_so,
                        group[2].rm_eo - group[2].rm_so - 1);
                used += atoi(tmp) * 1024;
            }
            else if (! regexec(&re_free, buf, 3, group, 0))
            {
                memset(tmp, 0, BUFSIZ);
                strncpy(tmp, buf + group[2].rm_so,
                        group[2].rm_eo - group[2].rm_so - 1);
                used -= atoi(tmp) * 1024;
            }
        }
    }

    _fclose(fp);
    regfree(&re_used);
    regfree(&re_free);

#elif defined(__APPLE__) && defined(__MACH__)
#elif defined(__FreeBSD__)
#endif

    if (ret)
        mem->used = used;

    return ret;
}


bool get_mem_total(struct mem_info* mem)
{
    bool ret = false;

    int total = 0;
#if defined(__linux__)
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
                        group[1].rm_eo - group[1].rm_so - 1);

        total = atoi(tmp) * 1024;
        regfree(&re);
    }

    _fclose(fp);

#elif defined(__APPLE__) && defined(__MACH__)
#elif defined(__FreeBSD__)
#endif

    if (ret)
        mem->total = total;

    return ret;
}


bool get_mem_percent(struct mem_info* mem)
{
    bool ret = false;

    if (! mem->used)
        get_mem_used(mem);
    if (! mem->used)
        return ret;

    if (! mem->total)
        get_mem_total(mem);
    if (! mem->total)
        return ret;

    ret = true;
    mem->percent = percent(mem->used, mem->total);

    return ret;
}
