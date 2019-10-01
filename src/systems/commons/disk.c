#if defined(__linux__)
#   include "../linux/disk.h"
#endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"

#include "disk.h"


struct disk_info* init_disk()
{
    struct disk_info* disk;

    if ((disk = (struct disk_info*)malloc(sizeof(struct disk_info))))
        clear_disk(disk);

    return disk;
}


void clear_disk(struct disk_info* disk)
{
    memset(disk, 0, sizeof(struct disk_info));
}


bool get_disk_dev(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_dev(disk)))
        memset(disk->dev, 0, BUFSIZ);

    return ret;
}


bool get_disk_name(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_name(disk)))
        memset(disk->name, 0, BUFSIZ);

    return ret;
}


bool get_disk_mount(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_mount(disk)))
        memset(disk->mount, 0, BUFSIZ);

    return ret;
}


bool get_disk_part(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_part(disk)))
        memset(disk->part, 0, BUFSIZ);

    return ret;
}


bool get_disk_used(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_used(disk)))
        disk->used = 0;

    return ret;
}


bool get_disk_total(struct disk_info* disk)
{
    bool ret = false;

    if (! (ret = __get_disk_total(disk)))
        disk->total = 0;

    return ret;
}


bool get_disk_percent(struct disk_info* disk)
{
    if (! disk->used)
    {
        get_disk_used(disk);
        if (! disk->used)
            return false;
    }

    if (! disk->total)
    {
        get_disk_total(disk);
        if (! disk->total)
            return false;
    }

    disk->percent = percent(disk->used, disk->total);
    return true;
}
