#if defined(__linux__)

#include <regex.h>
#include <stdbool.h>
#include <string.h>

#include "../../utils/macros.h"
#include "../../utils/tools.h"
#include "../commons/cpu.h"

#include "cpu.h"

bool __get_cores(struct cpu_info* cpu)
{
    bool ret = false;
    FILE* fp = NULL;
    char buf[BUFSIZ];
    regex_t re;

    if ((ret = (fp = fopen("/proc/cpuinfo", "r")) &&
        ! regcomp(&re, "^processor", REG_EXTENDED)))
    {
        while (fgets(buf, BUFSIZ, fp))
            if (! regexec(&re, buf, 0, NULL, 0))
                (cpu->cores)++;

        regfree(&re);
    }

    _fclose(fp);
    return ret;
}


bool __get_cpu(struct cpu_info* cpu, float* speed)
{
    bool ret = false;

    FILE* fp = NULL;
    char buf[BUFSIZ];

    regex_t re;
    regmatch_t group[2];

    char** paths = NULL;

    char* base = "/sys/devices/system/cpu/";
    char* target = "(bios_limit|(scaling|cpuinfo)_max_freq)$";

    int tmp = 0;
    int count;

    int i = -1;
    bool cond = false;

    if ((fp = fopen("/proc/cpuinfo", "r")) &&
        ! regcomp(&re, "model name\\s+: (.*)\n", REG_EXTENDED))
    {
        while (! ret && fgets(buf, BUFSIZ, fp))
            if ((ret = ! regexec(&re, buf, 2, group, 0)))
                strncpy(cpu->cpu, buf + group[1].rm_so,
                        group[1].rm_eo - group[1].rm_so);

        regfree(&re);
    }

    _fclose(fp);

    if ((paths = find_all(base, target, BUFSIZ, &count)))
    {
        while (! cond && ++i < count)
        {
            if ((fp = fopen(paths[i], "r")) &&
                fgets(buf, BUFSIZ, fp))
            {
                sscanf(buf, "%d", &tmp);
                cond = tmp;
            }
        }

        if (tmp)
            *speed = (double)tmp / 1000000;
    }

    _fclose(fp);

    if (paths)
    {
        for (i = 0; i < count; i++)
            _free(paths[i]);
        _free(paths);
    }

    return ret;
}


bool __get_load(struct cpu_info* cpu)
{
    bool ret = false;

    FILE* fp = NULL;
    char buf[BUFSIZ];

    if ((ret = (fp = fopen("/proc/loadavg", "r")) &&
                fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%f %f %f", &(cpu->load[0]),
                                &(cpu->load[1]),
                                &(cpu->load[2]));
    }

    _fclose(fp);

    return ret;
}


bool __get_fan(struct cpu_info* cpu)
{
    bool ret = false;

    char path[BUFSIZ];
    char* base = "/sys/devices/platform/";
    char* pattern = "fan1_input$";

    FILE* fp = NULL;
    char buf[BUFSIZ];

    if (find(base, pattern, path, BUFSIZ) &&
        (ret = (fp = fopen(path, "r")) &&
        fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%d", &(cpu->fan));
    }

    _fclose(fp);

    return ret;
}


bool __get_temp(struct cpu_info* cpu)
{
    bool ret = false;

    char** paths = NULL;
    char* path = NULL;

    char* base = "/sys/devices/platform/";
    char* target_1 = "name";
    char* target_2 = "temp[0-9]_input";

    int tmp = 0;
    int count;

    int i = -1;
    bool cond = false;

    FILE* fp = NULL;
    char buf[BUFSIZ];

    regex_t re;

    if ((paths = find_all(base, target_1, BUFSIZ, &count)) &&
        ! regcomp(&re, "temp", REG_EXTENDED))
    {
        while (! cond && ++i < count)
        {
            if ((fp = fopen(paths[i], "r")))
            {
                cond = fgets(buf, BUFSIZ, fp) && ! regexec(&re, buf, 0, NULL, 0);
                fclose(fp);
                fp = NULL;
            }
        }

        regfree(&re);

        if (cond)
        {
            path = (char*)malloc(BUFSIZ * sizeof(char));
            strncpy(path, paths[i], BUFSIZ);
            path[strlen(path) - 4] = '\0';

            for (i = 0; i < count; i++)
                _free(paths[i]);
            _free(paths);

            if ((paths = find_all(path, target_2, BUFSIZ, &count)))
            {
                i = -1;
                cond = false;

                while (! cond && ++i < count)
                {
                    if ((fp = fopen(paths[i], "r")) &&
                        fgets(buf, BUFSIZ, fp))
                    {
                        sscanf(buf, "%d", &tmp);
                        cond = tmp;
                    }
                }

                if (tmp)
                {
                    cpu->temp = (double)tmp / 1000;
                    ret = true;
                }
            }

            _free(path);
        }
    }

    _fclose(fp);

    if (paths)
    {
        for (i = 0; i < count; i++)
            _free(paths[i]);
        _free(paths);
    }

    return ret;
}


bool __get_uptime(struct cpu_info* cpu)
{
    bool ret = false;

    FILE* fp = NULL;
    char buf[BUFSIZ];

    if ((ret = (fp = fopen("/proc/uptime", "r")) &&
                fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%d", &(cpu->uptime));
    }

    _fclose(fp);

    return ret;
}

#endif
