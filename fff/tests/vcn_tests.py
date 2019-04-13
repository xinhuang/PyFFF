from unittest import TestCase

import fff


class VCNTests(TestCase):

    def test_parse_data_runs_empty(self):
        input = b'\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(0, len(actual))

    def test_vcn_empty(self):
        input = b'\x00'

        sut = fff.ntfs.VCN(input)

        self.assertEqual(0, sut.count)

    def test_parse_data_runs_non_fragmented(self):
        input = b'\x21\x18\x34\x56\x00'

        offset, actual = fff.ntfs.parse_data_runs(input, 0)

        self.assertEqual(len(input), offset)
        self.assertEqual(1, len(actual))
        self.assertEqual(0x18, actual[0].length)
        self.assertEqual(0x5634, actual[0].offset)

    def test_vcn_data_runs_non_fragmented(self):
        input = b'\x21\x18\x34\x56\x00'

        sut = fff.ntfs.VCN(input)

        self.assertEqual(0x18, sut.count)
        self.assertEqual(0x5634, sut[0])
        self.assertEqual(0x18 + 0x5634 - 1, sut[-1])
        self.assertEqual(list(range(0x5634, 0x18+0x5634)), sut[:])

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
