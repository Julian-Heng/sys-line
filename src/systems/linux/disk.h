#ifndef LINUX_DISK_H
#define LINUX_DISK_H
#if defined(__linux__)

#include <stdbool.h>
#include "../commons/disk.h"

#define MTAB_FILE "/etc/mtab"
#define UEVENT_REG "\\/dev\\/([^0-9]+)([0-9]+)"
#define NAME_REG "^PARTNAME=([a-zA-Z0-9_-]*)"

typedef enum mntnet_opts
{
    FSNAME,
    DIR,
    TYPE,
    OPTS
} mntnet_opts;

bool __get_disk_dev(struct disk_info*);
bool __get_disk_name(struct disk_info*);
bool __get_disk_mount(struct disk_info*);
bool __get_disk_part(struct disk_info*);
bool __get_disk_used(struct disk_info*);
bool __get_disk_total(struct disk_info*);

#endif
#endif
