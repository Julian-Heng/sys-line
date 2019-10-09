#if defined(__linux__)

#include <mntent.h>
#include <regex.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <sys/statvfs.h>
#include <sys/types.h>
#include <unistd.h>

#include "../../utils/macros.h"
#include "../../utils/tools.h"

#include "../commons/disk.h"

#include "disk.h"

static bool mount_to_device(char*, char*, int);
//static bool device_to_mount(char*, char*, int);
static bool query_mntent(char*, int, char*, int);
static char* get_sysfs_path(struct disk_info*);
static struct statvfs get_fs_stat(struct disk_info*);


bool __get_disk_dev(struct disk_info* disk)
{
    return mount_to_device("/", disk->dev, BUFSIZ);
}


bool __get_disk_name(struct disk_info* disk)
{
    bool ret = false;
    char uevent_path[BUFSIZ];

    FILE* fp = NULL;
    char buf[BUFSIZ];

    regex_t re;
    regmatch_t group[2];

    if (! strncmp(disk->dev, "", BUFSIZ) && ! __get_disk_dev(disk))
        return false;

    snprintf(uevent_path, BUFSIZ, "%s/uevent", get_sysfs_path(disk));

    if ((ret = (file_exist(uevent_path) &&
        (fp = fopen(uevent_path, "r")) &&
        ! regcomp(&re, NAME_REG, REG_EXTENDED))))
    {
        while (fgets(buf, BUFSIZ, fp))
            if (! regexec(&re, buf, 2, group, 0))
                strncpy(disk->name, buf + group[1].rm_so,
                                    group[1].rm_eo - group[1].rm_so);
    }

    _fclose(fp);
    regfree(&re);

    return ret;
}


bool __get_disk_mount(struct disk_info* disk)
{
    if (! strncmp(disk->dev, "", BUFSIZ) && ! __get_disk_dev(disk))
        return false;

    return query_mntent(disk->dev, DIR, disk->mount, BUFSIZ);
}


bool __get_disk_part(struct disk_info* disk)
{
    if (! strncmp(disk->dev, "", BUFSIZ) && ! __get_disk_dev(disk))
        return false;

    return query_mntent(disk->dev, TYPE, disk->part, BUFSIZ);
}


bool __get_disk_used(struct disk_info* disk)
{
    struct statvfs fs;

    if (! strncmp(disk->dev, "", BUFSIZ) && ! __get_disk_dev(disk))
        return false;

    fs = get_fs_stat(disk);
    disk->used = (fs.f_blocks - fs.f_bfree) * fs.f_frsize;
    return true;
}


bool __get_disk_total(struct disk_info* disk)
{
    struct statvfs fs;

    if (! strncmp(disk->dev, "", BUFSIZ) && ! __get_disk_dev(disk))
        return false;

    fs = get_fs_stat(disk);
    disk->total = fs.f_blocks * fs.f_frsize;
    return true;
}


static bool mount_to_device(char* mount, char* dest, int size)
{
    FILE* fp = NULL;
    struct mntent* fs = NULL;
    bool ret = false;

    fp = setmntent(MTAB_FILE, "r");
    while ((fs = getmntent(fp)) && strcmp(mount, fs->mnt_dir));

    if (fs)
    {
        strncpy(dest, fs->mnt_fsname, size);
        ret = true;
    }

    _fclose(fp);

    return ret;
}


/*
static bool device_to_mount(char* device, char* dest, int size)
{
    FILE* fp = NULL;
    struct mntent* fs = NULL;
    bool ret = false;

    fp = setmntent(MTAB_FILE, "r");
    while ((fs = getmntent(fp)) && strcmp(device, fs->mnt_fsname));

    if (fs)
    {
        strncpy(dest, fs->mnt_dir, size);
        ret = true;
    }

    _fclose(fp);

    return ret;
}
*/


static bool query_mntent(char* device, int query, char* dest, int size)
{
    FILE* fp = NULL;
    struct mntent* fs = NULL;
    bool ret = false;

    fp = setmntent(MTAB_FILE, "r");
    while ((fs = getmntent(fp)) && strcmp(device, fs->mnt_fsname));

    if (fs)
    {
        switch(query)
        {
            case FSNAME: strncpy(dest, fs->mnt_fsname, size); break;
            case DIR: strncpy(dest, fs->mnt_dir, size); break;
            case TYPE: strncpy(dest, fs->mnt_type, size); break;
            case OPTS: strncpy(dest, fs->mnt_opts, size); break;
        }

        ret = true;
    }

    _fclose(fp);

    return ret;
}


static char* get_sysfs_path(struct disk_info* disk)
{
    static char path[BUFSIZ];
    static bool is_set = false;

    char extract[2][8];

    regex_t re;
    regmatch_t group[3];

    if (! is_set)
    {
        if (! regcomp(&re, UEVENT_REG, REG_EXTENDED))
        {
            memset(extract[0], 0, 8);
            memset(extract[1], 0, 8);

            if (! regexec(&re, disk->dev, 3, group, 0))
            {
                strncpy(extract[0], disk->dev + group[1].rm_so,
                                    group[1].rm_eo - group[1].rm_so);
                strncpy(extract[1], disk->dev + group[2].rm_so,
                                    group[2].rm_eo - group[2].rm_so);
            }

            regfree(&re);
        }

        snprintf(path, BUFSIZ, "/sys/block/%s/%s%s", extract[0],
                                                     extract[0],
                                                     extract[1]);
        is_set = true;
    }

    return path;
}


static struct statvfs get_fs_stat(struct disk_info* disk)
{
    static struct statvfs fs_stat;
    static bool is_set = false;

    if (! is_set)
    {
        statvfs(disk->mount, &fs_stat);
        is_set = true;
    }

    return fs_stat;
}

#endif
