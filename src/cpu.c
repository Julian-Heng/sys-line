#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#if defined(__APPLE__) && defined(__MACH__)
#include <sys/types.h>
#include <sys/sysctl.h>
#endif

#include "cpu.h"

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

#if defined(__APPLE__) && defined(__MACH__)
    size_t len = sizeof(cores);

    ret = ! sysctlbyname("hw.logicalcpu_max", &cores, &len, NULL, 0);
#endif

    if (ret)
        cpu->cores = cores;

    return ret;
}


bool get_cpu(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__APPLE__) && defined(__MACH__)
    size_t len = sizeof(cpu->cpu);

    ret = ! sysctlbyname("machdep.cpu.brand_string", cpu->cpu, &len, NULL, 0);
#endif

    return ret;
}


bool get_load(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__APPLE__) && defined(__MACH__)
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

    if (cpu->cores == 0)
        get_cores(cpu);
    if (cpu->cores == 0)
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


bool get_uptime(struct cpu_info* cpu)
{
    bool ret = false;

#if defined(__APPLE__) && defined(__MACH__)
    struct timeval uptime;
    size_t len = sizeof(uptime);

    ret = ! sysctlbyname("kern.boottime", &uptime, &len, NULL, 0);
    cpu->uptime = (unsigned long)time(NULL) - uptime.tv_sec;
#endif

    return ret;
}
