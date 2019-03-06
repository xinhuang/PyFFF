

# Prototype

    import fff
    from hexdump import hexdump as hd
    
    with fff.DiskImage('disk1.dd.zip') as disk:
        print(hd(disk.volume.sectors[0]))
        print(disk.volume)
    
        partitions = disk.volume.partitions
    
        part = [p for p in partitions if p.filesystem.format == fff.FAT32][0]
        print(part.boot_sector.hexdump())
        print(part.boot_sector[0:-1])
    
        print([e for e in part.root_dir.entries if e.is_allocated()])
    
        files = list([e for e in part.root_dir.entries
    		  if e.is_allocated() and e.is_file()])
        print([f.slack_space[:4] for f in files])
    
        ntfs = [p for p in partitions if p.filesystem.format == fff.NTFS][0]
    
        print(ntfs.MFT)
        print(ntfs.MFT.entries[5])
        print(ntfs.MFT.entries['.'])

