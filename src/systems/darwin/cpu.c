#if defined(__APPLE__) && defined(__MACH__)

#include <sys/types.h>
#include <sys/sysctl.h>

#include <stdbool.h>
#include <stdlib.h>

#include "../commons/cpu.h"

#include "cpu.h"


bool __get_cores(struct cpu_info* cpu)
{
    bool ret = false;

    size_t len = sizeof(cpu->cores);
    ret = ! sysctlbyname("hw.logicalcpu_max", &(cpu->cores), &len, NULL, 0);

    return ret;
}


bool __get_cpu(struct cpu_info* cpu, float* speed)
{
    bool ret = false;

    size_t len = BUFSIZ;
    ret = ! sysctlbyname("machdep.cpu.brand_string", cpu->cpu, &len, NULL, 0);

    return ret;
}


bool __get_load(struct cpu_info* cpu)
{
    bool ret = false;

    struct loadavg load;
    size_t len = sizeof(load);

    ret = ! sysctlbyname("vm.loadavg", &load, &len, NULL, 0);
    for (int i = 0; i < 3; i++)
        cpu->load[i] = (float)load.ldavg[i] / load.fscale;

    return ret;
}


bool __get_fan(struct cpu_info* cpu)
{
    bool ret = false;

    return ret;
}


bool __get_temp(struct cpu_info* cpu)
{
    bool ret = false;

    return ret;
}


bool __get_uptime(struct cpu_info* cpu)
{
    bool ret = false;

    struct timeval uptime;
    size_t len = sizeof(uptime);

    ret = ! sysctlbyname("kern.boottime", &uptime, &len, NULL, 0);
    cpu->uptime = (unsigned long)time(NULL) - uptime.tv_sec;

    return ret;
}
#endif
