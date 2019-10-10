#if defined(__linux__)
#   include "../linux/disk.h"
#elif defined(__APPLE__) && defined(__MACH__)
#   include "../darwin/disk.h"
#endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/statvfs.h>

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
    if (! strncmp(disk->mount, "", BUFSIZ) && ! __get_disk_mount(disk))
        return false;

    struct statvfs fs;
    statvfs(disk->mount, &fs);
    disk->used = (fs.f_blocks - fs.f_bfree) * fs.f_frsize;

    return true;
}


bool get_disk_total(struct disk_info* disk)
{
    if (! strncmp(disk->mount, "", BUFSIZ) && ! __get_disk_mount(disk))
        return false;

    struct statvfs fs;
    statvfs(disk->mount, &fs);
    disk->total = fs.f_blocks * fs.f_frsize;

    return true;
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
