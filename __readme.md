

# Example

    import fff
    from fff.util import *
    
    with fff.DiskImage('disk1.dd.zip') as disk:
        print(hd(disk.volume.sectors[0]))
        print(disk.volume)
    
        partitions = disk.volume.partitions
    
        part = next(p for p in partitions if p.filesystem.fs_type == 'NTFS')
        print(hd(part.boot_sector.raw))
        print(part.boot_sector)
    
        ntfs = part.filesystem
    
        print(ntfs.mft)
        print(ntfs.mft.find(inode=5))        # Root Directory MFT Entry
    
        print([e for e in ntfs.root.list() if e.is_allocated])
    
        files = list([e for e in ntfs.root.list()
    		  if e.is_allocated and e.is_file])
        print([f.slack_space[:4] for f in files])


# Installation

This project is not on PyPI. You need to build from the source code.

    # git clone
    $ cd PyFFF
    
    # Create virtual environment
    $ virtualenv -p python3 .
    $ source bin/active
    
    # Installing the dependencies
    $ pip install -r requirements.txt
    
    # Tests can be run using =nosetests=, however due to copy-right reason,
    # the test data is not submitted.
    # You can skip this step for now.
    $ nosetests
    
    # Create installation package
    $ python setup.py sdist
    
    # Install to user library
    $ pip3 install dist/PyFFF-0.1.0.tar.gz --user


# Contribution

Contributions are welcome, however this project is still under active refactoring
and many details haven't settle down yet.

If you would like to submit a pull request, either fixing a bug or adding a new feature,
please be minded that:

1.  Type annotation of [mypy](https://mypy.readthedocs.io/en/latest/) is required for new code.
2.  Test case should be added.
3.  Please make small commits. The pull request can be large.
4.  Try to make the code as clean as possible.


# License

GPLv3

