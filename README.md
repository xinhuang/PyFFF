
# Table of Contents

1.  [Prototype](#orgf8dd5f8)



<a id="orgf8dd5f8"></a>

# Prototype

    import fff
    
    with fff.DiskImage('disk1.dd', type='raw') as disk:
        disk.volume.hexdump()
        print(disk.volume)
    
        partitions = disk.volume.partitions
    
        part = [p for p in partitions if p.format == fff.FAT32][0]
        print(part.boot_sector.hexdump())
        print(part.boot_sector)
    
        print([e for e in part.root_dir.entries if e.is_allocated()])
    
        files = list([e for e in part.root_dir.entries
                      if e.is_allocated() and e.is_file()])
        print([f.slack_space[:4] for f in files])

