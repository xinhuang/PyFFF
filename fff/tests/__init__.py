from unittest import TestCase

import fff


class ZipImageTests(TestCase):

    sut = None

    @classmethod
    def setUpClass(cls):
        ZipImageTests.sut = fff.DiskImage('/Users/xin/practice1.dd.zip')

    @classmethod
    def tearDownClass(cls):
        ZipImageTests.sut.close()
        ZipImageTests.sut = None

    def setUp(self):
        self.sut = ZipImageTests.sut

    def tearDown(self):
        self.sut = None

    def test_load_zip(self):
        self.assertFalse(self.sut.volume is None)

    def test_FAT16_filesystem(self):
        fs = self.sut.volume[10].filesystem

        self.assertFalse(fs is None)
        self.assertTrue(fs.fs_type == 'FAT16')

    def test_NTFS_filesystem(self):
        fs = self.sut.volume[14].filesystem

        self.assertFalse(fs is None)
        self.assertTrue(fs.fs_type == 'NTFS')

        self.assertEqual(b'\xeb\x52\x90', fs.boot_sector.jmp)
