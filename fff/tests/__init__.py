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

    def test_volume_tabulate(self):
        self.sut.volume.tabulate()

    def test_FAT16_filesystem(self):
        fs = self.sut.volume[10].filesystem

        self.assertFalse(fs is None)
        self.assertTrue(fs.fs_type == 'FAT16')

    def test_volume_access_sector_0(self):
        expect = b'\xeb<\x90mkdosfs'
        actual = self.sut.volume[10].sectors[0][:len(expect)]

        self.assertEqual(expect, actual)

    def test_NTFS_filesystem(self):
        fs = self.sut.volume[14].filesystem

        self.assertFalse(fs is None)
        self.assertTrue(fs.fs_type == 'NTFS')

        self.assertEqual(b'\xeb\x52\x90', fs.boot_sector.jmp)

    def test_NTFS_access_sector_0(self):
        fs = self.sut.volume[14].filesystem

        expect = b'\xEB\x52\x90NTFS    \x00'
        actual = fs.sectors[0][:len(expect)]

        self.assertEqual(expect, actual)

    def test_NTFS_access_cluster_0(self):
        fs = self.sut.volume[14].filesystem

        expect = b'\xEB\x52\x90NTFS    \x00'
        actual = fs.clusters[0][:len(expect)]

        self.assertEqual(expect, actual)
