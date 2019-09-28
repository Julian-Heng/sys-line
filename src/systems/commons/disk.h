#ifndef COMMONS_DISK_H
#define COMMONS_DISK_H

#include <stdbool.h>
#include <stdio.h>

struct disk_info
{
    char dev[BUFSIZ];
    char name[BUFSIZ];
    char mount[BUFSIZ];
    char part[BUFSIZ];
    long long used;
    long long total;
    float percent;
};


struct disk_info* init_disk(void);
bool get_disk_dev(struct disk_info*);
bool get_disk_name(struct disk_info*);
bool get_disk_mount(struct disk_info*);
bool get_disk_part(struct disk_info*);
bool get_disk_used(struct disk_info*);
bool get_disk_total(struct disk_info*);
bool get_disk_percent(struct disk_info*);

#endif
