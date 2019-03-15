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
        self.sut = NTFSTests.sut

    def tearDown(self):
        self.sut = None

    def test_count_of_MFT_entries(self):
        self.skipTest('TODO: Parse NTFS MFT')
        fs = self.sut.volume[14].filesystem

        self.assertEqual(251, len(fs.mft.entries))
