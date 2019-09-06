#if defined(__linux__)
#   define _DEFAULT_SOURCE
#   include <regex.h>
#elif defined(__APPLE__) && defined(__MACH__) || defined(__FreeBSD__)
#   include <sys/types.h>
#   include <sys/sysctl.h>
#endif
#if defined(__FreeBSD__)
#   include <sys/resource.h>
#   include <time.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "cpu.h"
#include "tools.h"
#include "macros.h"


struct cpu_info* init_cpu(void)
{
    struct cpu_info* cpu;

    if ((cpu = (struct cpu_info*)malloc(sizeof(struct cpu_info))))
    {
        cpu->cores = 0;
        memset(cpu->cpu, '\0', BUFSIZ);

        for (int i = 0; i < 3; i++)
            cpu->load[i] = 0.0;

        cpu->cpu_usage = 0.0;
        cpu->fan = 0;
        cpu->temp = 0.0;
        cpu->uptime = 0;
    }

    return cpu;
}


bool get_cores(struct cpu_info* cpu)
{
    bool ret = false;
    int cores = 0;

#if defined(__linux__)
    FILE* fp;
    char buf[BUFSIZ];
    regex_t re;

    if ((ret = (fp = fopen("/proc/cpuinfo", "r")) &&
        ! regcomp(&re, "^processor", REG_EXTENDED)))
    {
        while (fgets(buf, BUFSIZ, fp))
            if (! regexec(&re, buf, 0, NULL, 0))
                cores++;

        regfree(&re);
    }

    if (fp)
        fclose(fp);

#elif defined(__APPLE__) && defined(__MACH__)
    size_t len = sizeof(cores);
    ret = ! sysctlbyname("hw.logicalcpu_max", &cores, &len, NULL, 0);

#elif defined(__FreeBSD__)
    size_t len = sizeof(cores);
    ret = ! sysctlbyname("hw.ncpu", &cores, &len, NULL, 0);

#endif

    if (ret)
        cpu->cores = cores;

    return ret;
}


bool get_cpu(struct cpu_info* cpu)
{
    bool ret = false;

    float speed = 0.0;
    char cpu_regex[BUFSIZ];
    char cpu_replace[BUFSIZ];
#if defined(__linux__)
    FILE* fp;
    char buf[BUFSIZ];

    regex_t re;
    regmatch_t group[2];

    char** paths = NULL;
    char* path = NULL;

    char* base = "/sys/devices/system/cpu/";
    char* target = "(bios_limit|(scaling|cpuinfo)_max_freq)$";

    int tmp = 0;
    float _speed = 0.0;
    int count;

    int i = -1;
    bool cond = false;

    if ((fp = fopen("/proc/cpuinfo", "r")) &&
        ! regcomp(&re, "model name\\s+: (.*)", REG_EXTENDED))
    {
        while (! ret && fgets(buf, BUFSIZ, fp))
            if ((ret = ! regexec(&re, buf, 2, group, 0)))
                strncpy(cpu->cpu, buf + group[1].rm_so,
                        group[1].rm_eo - group[1].rm_so - 1);

        fclose(fp);
        regfree(&re);
    }

    if ((paths = find_all(base, target, BUFSIZ, &count)))
    {
        while (! cond && ++i < count)
            if ((fp = fopen(paths[i], "r")) &&
                fgets(buf, BUFSIZ, fp))
            {
                sscanf(buf, "%d", &tmp);
                cond = tmp;
                fclose(fp);
            }

        if (tmp)
            speed = (double)tmp / 1000000;
    }

    if (paths)
    {
        for (i = 0; i < count; i++)
            _free(paths[i]);
        _free(paths);
    }


#elif defined(__APPLE__) && defined(__MACH__)
    size_t len = BUFSIZ;
    ret = ! sysctlbyname("machdep.cpu.brand_string", cpu->cpu, &len, NULL, 0);

#elif defined(__FreeBSD__)
    size_t len = BUFSIZ;
    ret = ! sysctlbyname("hw.model", cpu->cpu, &len, NULL, 0);

#endif

    if (speed > 0.0)
    {
        snprintf(cpu_replace, BUFSIZ, "(%d) @ %0.1fGHz", cpu->cores, speed);
        snprintf(cpu_regex, BUFSIZ, "@ [0-9]+\\.[0-9]+GHz");
    }
    else
    {
        snprintf(cpu_replace, BUFSIZ, "(%d) @", cpu->cores);
        snprintf(cpu_regex, BUFSIZ, "@");
    }

    re_replace(cpu_regex, cpu_replace, cpu->cpu, BUFSIZ);
    re_replace_all("CPU|\\((R|TM)\\)", "", cpu->cpu, BUFSIZ);
    trim(cpu->cpu);

    return ret;
}


bool get_load(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__linux__)
    FILE* fp;
    char buf[BUFSIZ];

    if ((ret = (fp = fopen("/proc/loadavg", "r")) &&
                fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%f %f %f", &(cpu->load[0]),
                                &(cpu->load[1]),
                                &(cpu->load[2]));
        fclose(fp);
    }

#elif defined(__APPLE__) && defined(__MACH__) || defined(__FreeBSD__)
    struct loadavg load;
    size_t len = sizeof(load);

    ret = ! sysctlbyname("vm.loadavg", &load, &len, NULL, 0);
    for (int i = 0; i < 3; i++)
        cpu->load[i] = (float)load.ldavg[i] / load.fscale;

#endif

    return ret;
}


bool get_cpu_usage(struct cpu_info* cpu)
{
    bool ret = false;
    FILE* ps;
    char buf[BUFSIZ];
    float val = 0.0;

    if (! cpu->cores)
        get_cores(cpu);
    if (! cpu->cores)
        return ret;

    if ((ret = (ps = popen("ps -e -o %cpu", "r"))))
    {
        memset(buf, '\0', BUFSIZ);

        while (fgets(buf, BUFSIZ, ps))
            if (sscanf(buf, "%f", &val) == 1)
                cpu->cpu_usage += val;

        cpu->cpu_usage /= cpu->cores;
        pclose(ps);
    }

    return ret;
}


bool get_fan(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__linux__)
    char path[BUFSIZ];
    char* base = "/sys/devices/platform/";
    char* pattern = "fan1_input$";

    FILE* fp;
    char buf[BUFSIZ];

    if (find(base, pattern, path, BUFSIZ) &&
        (ret = (fp = fopen(path, "r")) &&
        fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%d", &(cpu->fan));
        fclose(fp);
    }
#elif defined(__APPLE__) && defined(__MACH__)
#elif defined(__FreeBSD__)
#endif

    return ret;
}


bool get_temp(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__linux__)
    char** paths = NULL;
    char* path = NULL;

    char* base = "/sys/devices/platform/";
    char* target_1 = "name";
    char* target_2 = "temp[0-9]_input";

    int tmp = 0;
    int count;

    int i = -1;
    bool cond = false;

    FILE* fp;
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
                    if ((fp = fopen(paths[i], "r")) &&
                        fgets(buf, BUFSIZ, fp))
                    {
                        sscanf(buf, "%d", &tmp);
                        cond = tmp;
                        fclose(fp);
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

    if (paths)
    {
        for (i = 0; i < count; i++)
            _free(paths[i]);
        _free(paths);
    }

#elif defined(__APPLE__) && defined(__MACH__)
#elif defined(__FreeBSD__)
#endif

    return ret;
}


bool get_uptime(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__linux__)
    FILE* fp;
    char buf[BUFSIZ];

    if ((ret = (fp = fopen("/proc/uptime", "r")) &&
                fgets(buf, BUFSIZ, fp)))
    {
        sscanf(buf, "%d", &(cpu->uptime));
        fclose(fp);
    }

#elif defined(__APPLE__) && defined(__MACH__) || defined(__FreeBSD__)
    struct timeval uptime;
    size_t len = sizeof(uptime);

    ret = ! sysctlbyname("kern.boottime", &uptime, &len, NULL, 0);
    cpu->uptime = (unsigned long)time(NULL) - uptime.tv_sec;

#endif

    return ret;
}
