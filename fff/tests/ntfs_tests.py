from unittest import TestCase
import hashlib

import fff


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
        self.assertTrue(self.sut.mft.mft_entry.attrs)

    def test_tabulate_StandardInformation(self):
        sut = self.sut.mft.mft_entry.attrs[0]

        self.assertEqual(116444736000000000, sut.ctime)
        self.assertEqual(116444736000000000, sut.atime)
        self.assertEqual(116444736000000000, sut.mtime)
        self.assertEqual(116444736000000000, sut.rtime)
        self.assertEqual(0x6, sut.perm)

        self.sut.mft.mft_entry.attrs[0].tabulate()

    def test_MFT_FileName(self):
        self.assertEqual('$MFT', self.sut.mft.mft_entry.attrs[1].filename)

        self.sut.mft.mft_entry.attrs[1].tabulate()

    def test_tabulate_BootSector(self):
        self.sut.boot_sector.tabulate()

    def test_parse_data_runs_empty(self):
        input = b'\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(0, len(actual))

    def test_parse_data_runs_non_fragmented(self):
        input = b'\x21\x18\x34\x56\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(1, len(actual))
        self.assertEqual(0x18, actual[0].length)
        self.assertEqual(0x5634, actual[0].offset)

    def test_parse_data_runs_fragmented(self):
        input = b'\x31\x38\x73\x25\x34\x32\x14\x01\xE5\x11\x02\x31\x42\xAA\x00\x03\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(3, len(actual))

        self.assertEqual(0x38, actual[0].length)
        self.assertEqual(0x342573, actual[0].offset)

        self.assertEqual(0x0114, actual[1].length)
        self.assertEqual(0x0211E5 + 0x342573, actual[1].offset)

        self.assertEqual(0x42, actual[2].length)
        self.assertEqual(0x300AA + 0x0211E5 + 0x342573, actual[2].offset)

    def test_parse_data_runs_sparse_unfragmented(self):
        input = b'\x11\x30\x20\x01\x60\x11\x10\x30\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(3, len(actual))

        self.assertEqual(0x30, actual[0].length)
        self.assertEqual(0x20, actual[0].offset)

        self.assertEqual(0x60, actual[1].length)
        self.assertEqual(None, actual[1].offset)

        self.assertEqual(0x10, actual[2].length)
        self.assertEqual(0x20 + 0x30, actual[2].offset)

    def test_parse_data_runs_scrambled(self):
        input = b'\x11\x30\x60\x21\x10\x00\x01\x11\x20\xE0\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(3, len(actual))

        self.assertEqual(0x30, actual[0].length)
        self.assertEqual(0x60, actual[0].offset)

        self.assertEqual(0x10, actual[1].length)
        self.assertEqual(0x60 + 0x100, actual[1].offset)

        self.assertEqual(0x20, actual[2].length)
        self.assertEqual(0x60 + 0x100 - 0x20, actual[2].offset)

    def test_MFT_data_runs(self):
        data_attr = self.sut.mft.attr(type_id='$DATA')

        self.assertEqual(1, len(data_attr.data_runs))
        self.assertEqual(251, data_attr.data_runs[0].length)
        self.assertEqual(16, data_attr.data_runs[0].offset)

    def test_read_mft_first_5_bytes(self):
        actual0 = next(self.sut.mft.read2(skip=0, bsize=1, count=5)).decode()
        actual1 = next(self.sut.mft.read2(skip=0, bsize=5, count=1)).decode()

        self.assertEqual('FILE0', actual0)
        self.assertEqual('FILE0', actual1)
