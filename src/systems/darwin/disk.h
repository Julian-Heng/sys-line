#ifndef DARWIN_DISK_H
#define DARWIN_DISK_H
#if defined(__APPLE__) && defined(__MACH__)

#include <stdbool.h>
#include "../commons/disk.h"

enum fd_opt
{
    DISK,
    MOUNT
};

bool __get_disk_dev(struct disk_info*);
bool __get_disk_name(struct disk_info*);
bool __get_disk_mount(struct disk_info*);
bool __get_disk_part(struct disk_info*);

#endif
#endif
