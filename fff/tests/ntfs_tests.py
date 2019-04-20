import fff

from unittest import TestCase
import hashlib
import datetime


class NTFSTests(TestCase):

    sut = None

    @classmethod
    def setUpClass(cls):
        NTFSTests.sut = fff.DiskImage('/Users/xin/practice1.dd.zip')

    @classmethod
    def tearDownClass(cls):
        NTFSTests.sut.close()
        NTFSTests.sut = None

    def setUp(self):
        self.disk = NTFSTests.sut
        self.sut = self.disk.volume[14].filesystem

    def tearDown(self):
        self.sut = None
        self.disk = None

    def test_count_of_MFT_entries(self):
        self.skipTest('TODO: Parse NTFS MFT')

        self.assertEqual(251, len(self.sut.mft.entries))

    def test_mft_entry_attributes(self):
        self.assertTrue(self.sut.mft.mft_entry.attrs())

    def test_tabulate_StandardInformation(self):
        sut = self.sut.mft.mft_entry.attrs(type_id=0x10)[0]
        expect = datetime.datetime(1970, 1, 1)

        self.assertEqual(expect, sut.ctime)
        self.assertEqual(expect, sut.atime)
        self.assertEqual(expect, sut.mtime)
        self.assertEqual(expect, sut.rtime)
        self.assertEqual(0x6, sut.perm)

        sut.tabulate()

    def test_MFT_FileName(self):
        actual = self.sut.mft.mft_entry.attrs(type_id=0x30)[0]

        self.assertEqual('$MFT', actual.filename)

        actual.tabulate()

    def test_tabulate_BootSector(self):
        self.sut.boot_sector.tabulate()

    def test_MFT_data_runs(self):
        data_attr = self.sut.mft.attr(type_id='$DATA')

        self.assertEqual(1, len(data_attr.vcn.drs))
        self.assertEqual(251, data_attr.vcn.drs[0].length)
        self.assertEqual(16, data_attr.vcn.drs[0].offset)

    def test_read_mft_first_5_bytes(self):
        actual0 = next(self.sut.mft.read2(skip=0, bsize=1, count=5)).decode()
        actual1 = next(self.sut.mft.read2(skip=0, bsize=5, count=1)).decode()

        self.assertEqual('FILE0', actual0)
        self.assertEqual('FILE0', actual1)

    def test_get_file_size_inode_200(self):
        actual = self.sut.find(inode=200)

        self.assertIsNotNone(actual)
        self.assertEqual(4655616, actual.size)
        self.assertEqual(4656128, actual.allocated_size)

    def test_file_attr_inode_200(self):
        actual = self.sut.find(inode=200)

        self.assertTrue(actual.is_file)
        self.assertFalse(actual.is_dir)
        self.assertTrue(actual.is_allocated)

    def test_get_root_directory_tabulate(self):
        self.sut.root.tabulate()

    def test_root_dir_IndexRoot_child_vcn(self):
        root = self.sut.root

        self.assertEqual(0, root.attr(type_id='$INDEX_ROOT').entries[0].child_vcn)
