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

    def test_tabulate_StandardInformation(self):
        self.sut.mft.mft_entries[0].tabulate()

    def test_tabulate_BootSector(self):
        self.sut.boot_sector.tabulate()
