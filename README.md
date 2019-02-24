
# Table of Contents

1.  [Prototype](#orgfdaa490)



<a id="orgfdaa490"></a>

# Prototype

    import fff
    
    with fff.DiskImage('disk1.dd', type='raw') as disk:
        partitions = disk.partitions
        for p in partitions:
            print(p)
    
        part = [p for p in partitions if p.format == pens.FAT32][0]
        print(part.boot_sector)
        print([e for e in part.root_dir.entries if e.is_allocated()])
    
        files = list([e for e in part.root_dir.entries
                      if e.is_allocated() and e.is_file()])
        print([f.slack_space[:4] for f in files])

