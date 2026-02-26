"""
Tests for the Search Service — brand detection and search logic.

Covers:
  - Brand detection from query text
  - Default brand (sirket_genel) for generic queries
  - Multiple brand checks
"""

import pytest
from app.services.brand_detector import detect_brand, KNOWN_BRANDS, DEFAULT_BRAND


class TestBrandDetection:
    """Test brand detection logic."""

    def test_detect_pepsi(self):
        """Query containing 'pepsi' should detect pepsi brand."""
        assert detect_brand("Pepsi ürünleri nelerdir?") == "pepsi"

    def test_detect_pursu(self):
        """Query containing 'pürsu' should detect pürsu brand."""
        assert detect_brand("Pürsu su çeşitleri") == "pürsu"

    def test_detect_doganay(self):
        """Query containing 'doğanay' should detect doğanay brand."""
        assert detect_brand("Doğanay şalgam suyu fiyatı") == "doğanay"

    def test_detect_kizilayy(self):
        """Query containing 'kızılay' should detect kızılay brand."""
        assert detect_brand("Kızılay maden suyu") == "kızılay"

    def test_default_brand_generic_query(self):
        """Generic query should return sirket_genel."""
        assert detect_brand("Şirket hakkında bilgi") == DEFAULT_BRAND

    def test_default_brand_empty_match(self):
        """Query with no brand keywords should return default."""
        assert detect_brand("Fiyat listesi nedir?") == DEFAULT_BRAND

    def test_case_insensitive(self):
        """Brand detection should be case-insensitive."""
        assert detect_brand("PEPSI ürünleri") == "pepsi"
        assert detect_brand("pepsi ürünleri") == "pepsi"

    def test_all_known_brands(self):
        """Each known brand should be detectable."""
        for brand in KNOWN_BRANDS:
            assert detect_brand(f"Bilgi ver: {brand}") == brand
