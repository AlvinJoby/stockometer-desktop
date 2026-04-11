import unittest

from stockIndex.getIndex import get_index, get_index_display_name


class GetIndexTests(unittest.TestCase):
    def test_maps_known_exchange_aliases(self):
        self.assertEqual(get_index("NSI"), "^NSEI")
        self.assertEqual(get_index("BOM"), "^BSESN")
        self.assertEqual(get_index("PCX"), "^GSPC")

    def test_falls_back_to_symbol_suffix_when_exchange_is_missing(self):
        self.assertEqual(get_index(None, "RELIANCE.NS"), "^NSEI")
        self.assertEqual(get_index("", "TCS.BO"), "^BSESN")
        self.assertEqual(get_index(None, "SHOP.TO"), "^GSPTSE")

    def test_returns_none_for_unknown_market(self):
        self.assertIsNone(get_index("UNKNOWN", "ABC"))

    def test_returns_human_readable_index_display_names(self):
        self.assertEqual(get_index_display_name("^NSEI"), "NIFTY 50")
        self.assertEqual(get_index_display_name("^GSPC"), "S&P 500")
        self.assertEqual(get_index_display_name("^BSESN"), "SENSEX")


if __name__ == "__main__":
    unittest.main()
