#if defined(__APPLE__) && defined(__MACH__)

#include <sys/types.h>
#include <sys/sysctl.h>

#include <regex.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"
#include "../commons/mem.h"

#include "mem.h"


bool __get_mem_used(struct mem_info* mem)
{
    bool ret = false;
    long long used = 0;

    char buf[BUFSIZ];
    char tmp[BUFSIZ];

    FILE* ps = NULL;
    regex_t re;
    regmatch_t group[3];

    if ((ret = (ps = popen("vm_stat", "r"))) &&
        ! regcomp(&re, USED_REG, REG_EXTENDED))
    {
        memset(buf, 0, BUFSIZ);
        memset(tmp, 0, BUFSIZ);

        while (fgets(buf, BUFSIZ, ps))
        {
            if (! regexec(&re, buf, 3, group, 0))
            {
                memset(tmp, 0, BUFSIZ);
                strncpy(tmp, buf + group[2].rm_so,
                        group[2].rm_eo - group[2].rm_so);
                used += atoll(tmp);
            }
        }

        used <<= 12;
        regfree(&re);
    }

    _pclose(ps);

    if (ret)
        mem->used = used;

    return ret;
}


bool __get_mem_total(struct mem_info* mem)
{
    bool ret = false;
    long long total = 0;

    size_t len = sizeof(total);
    ret = ! sysctlbyname("hw.memsize", &total, &len, NULL, 0);

    if (ret)
        mem->total = total;

    return ret;
}
#endif
