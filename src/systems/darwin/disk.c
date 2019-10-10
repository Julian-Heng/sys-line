#if defined(__APPLE__) && defined(__MACH__)

#include "../commons/disk.h"

#include "disk.h"


bool __get_disk_dev(struct disk_info* disk)
{
    return false;
}


bool __get_disk_name(struct disk_info* disk)
{
    return false;
}


bool __get_disk_mount(struct disk_info* disk)
{
    return false;
}


bool __get_disk_part(struct disk_info* disk)
{
    return false;
}

#endif
