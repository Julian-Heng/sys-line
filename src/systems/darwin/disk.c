#if defined(__APPLE__) && defined(__MACH__)

#include <sys/mount.h>
#include <sys/param.h>
#include <sys/ucred.h>

#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"

#include "../commons/disk.h"

#include "disk.h"

static bool set_fs(struct disk_info*, char*, int);


bool __get_disk_dev(struct disk_info* disk)
{
    if (! set_fs(disk, "/", MOUNT))
        return false;

    strncpy(disk->dev, (disk->fs).f_mntfromname, BUFSIZ);
    return true;
}


bool __get_disk_name(struct disk_info* disk)
{
    return false;
}


bool __get_disk_mount(struct disk_info* disk)
{
    if (! set_fs(disk, "/", MOUNT))
        return false;

    strncpy(disk->mount, (disk->fs).f_mntonname, BUFSIZ);
    return true;
}


bool __get_disk_part(struct disk_info* disk)
{
    if (! set_fs(disk, "/", MOUNT))
        return false;

    strncpy(disk->part, (disk->fs).f_fstypename, BUFSIZ);
    return true;
}


static bool set_fs(struct disk_info* disk, char* query, int mode)
{
    int i = 0;
    size_t size_fs = 0;
    struct statfs* fs = NULL;

    if (! disk->fs_set)
    {
        size_fs = getmntinfo(&fs, MNT_NOWAIT);

        do
        {
            switch (mode)
            {
                case DISK:
                    if ((disk->fs_set = (! strcmp(query, fs[i].f_mntfromname))))
                        memcpy(&(disk->fs), fs + i, sizeof(struct statfs));
                    break;

                case MOUNT:
                    if ((disk->fs_set = (! strcmp(query, fs[i].f_mntonname))))
                        memcpy(&(disk->fs), fs + i, sizeof(struct statfs));
                    break;
            }
        } while (++i < size_fs && ! disk->fs_set);

        _free(fs);
    }

    return disk->fs_set;
}

#endif
