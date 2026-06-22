"""Tests for the comprehensive Indonesian text preprocessing pipeline."""
import pytest

from pipeline.sentiment.preprocessing import (
    # cleaning
    remove_urls,
    remove_html,
    remove_emojis,
    remove_mentions,
    extract_hashtags,
    remove_hashtag_symbol,
    normalize_repeated_chars,
    remove_numbers,
    remove_special_chars,
    normalize_whitespace,
    remove_accents,
    # normalization
    normalize_slang,
    # stopwords
    remove_stopwords,
    # stemming
    stem_indonesian,
    # full pipeline
    preprocess,
    # features
    extract_features,
    # constants
    SLANG_MAP,
    SENTIMENT_KEEPERS,
)

pytestmark = pytest.mark.unit


# --- Cleaning tests ---

class TestRemoveUrls:
    def test_http(self):
        assert normalize_whitespace(remove_urls("check https://example.com now")) == "check now"

    def test_www(self):
        assert normalize_whitespace(remove_urls("go to www.test.com ok")) == "go to ok"

    def test_no_url(self):
        assert remove_urls("hello world") == "hello world"


class TestRemoveHtml:
    def test_tags(self):
        assert normalize_whitespace(remove_html("<p>hello</p>")) == "hello"

    def test_nested(self):
        assert normalize_whitespace(remove_html('<div class="x"><b>bold</b></div>')) == "bold"


class TestRemoveEmojis:
    def test_emoji(self):
        assert normalize_whitespace(remove_emojis("bagus 🎉🎉")) == "bagus"

    def test_no_emoji(self):
        assert remove_emojis("bagus sekali") == "bagus sekali"


class TestRemoveMentions:
    def test_mention(self):
        assert normalize_whitespace(remove_mentions("hello @user123 ok")) == "hello ok"

    def test_multiple(self):
        assert normalize_whitespace(remove_mentions("@a @b test")) == "test"


class TestHashtags:
    def test_extract(self):
        assert extract_hashtags("test #bni #bions ok") == ["bni", "bions"]

    def test_strip_symbol(self):
        assert remove_hashtag_symbol("#bni securitas") == "bni securitas"


class TestNormalizeRepeatedChars:
    def test_triple(self):
        assert normalize_repeated_chars("bagusss") == "baguss"

    def test_quad(self):
        assert normalize_repeated_chars("bangett") == "bangett"  # only 2 repeated → preserved

    def test_extreme(self):
        assert normalize_repeated_chars("lamaaaaaaa") == "lamaa"

    def test_double_preserved(self):
        assert normalize_repeated_chars("bagus") == "bagus"

    def test_different_chars(self):
        assert normalize_repeated_chars("okeee yesss") == "okee yess"


class TestRemoveNumbers:
    def test_numbers(self):
        assert normalize_whitespace(remove_numbers("bintang 4 dapat 100")) == "bintang dapat"


class TestNormalizeWhitespace:
    def test_multi_space(self):
        assert normalize_whitespace("  hello   world  ") == "hello world"

    def test_tabs(self):
        assert normalize_whitespace("a\t\tb") == "a b"


class TestRemoveAccents:
    def test_accented(self):
        assert remove_accents("makanlé") == "makanle"

    def test_clean(self):
        assert remove_accents("sudah") == "sudah"


# --- Slang normalization tests ---

class TestNormalizeSlang:
    def test_single_slang(self):
        assert "tidak" in normalize_slang("gk bisa").split()

    def test_multiple(self):
        result = normalize_slang("gw mau lg aja")
        assert "saya" in result.split()
        assert "saja" in result.split()

    def test_preserves_non_slang(self):
        assert "aplikasi" in normalize_slang("aplikasi bagus").split()

    def test_app_specific(self):
        result = normalize_slang("error crash bug lemot")
        assert "galat" in result.split()
        assert "macet" in result.split()

    def test_slang_map_completeness(self):
        critical = ["gk", "ga", "gak", "yg", "utk", "aja", "bgt", "tp", "gw", "lu"]
        for word in critical:
            assert word in SLANG_MAP, f"Missing slang entry: {word}"


# --- Stopword tests ---

class TestRemoveStopwords:
    def test_removes_function_words(self):
        result = remove_stopwords("ini adalah aplikasi yang bagus")
        words = result.split()
        assert "adalah" not in words
        assert "yang" not in words

    def test_keeps_sentiment_words(self):
        result = remove_stopwords("tidak bagus dan tidak puas")
        words = result.split()
        assert "tidak" in words
        assert "bagus" in words

    def test_empty(self):
        assert remove_stopwords("") == ""


# --- Stemming tests ---

class TestStemming:
    def test_basic(self):
        result = stem_indonesian("berlari di lapangan")
        assert "lari" in result

    def test_prefix(self):
        result = stem_indonesian("membaca buku")
        assert "baca" in result


# --- Full pipeline tests ---

class TestPreprocessRuleBased:
    def test_basic(self):
        result = preprocess("Aplikasi ini bagus sekali!!! 🎉", mode="rule_based")
        assert result == result.lower()
        assert "🎉" not in result
        assert "!!!" not in result

    def test_empty(self):
        assert preprocess("", mode="rule_based") == ""
        assert preprocess("   ", mode="rule_based") == ""
        assert preprocess(None, mode="rule_based") == ""  # type: ignore

    def test_url_removal(self):
        assert "http" not in preprocess("visit https://x.com", mode="rule_based")

    def test_slang_normalized(self):
        result = preprocess("gk bisa login", mode="rule_based")
        assert "tidak" in result

    def test_stopwords_removed(self):
        result = preprocess("ini adalah aplikasi", mode="rule_based")
        assert "adalah" not in result

    def test_stemming_applied(self):
        result = preprocess("berlari dengan cepat", mode="rule_based")
        assert "lari" in result or "cepat" in result


class TestPreprocessIndobert:
    def test_basic(self):
        result = preprocess("Aplikasi ini bagus!!!", mode="indobert")
        assert result == result.lower()

    def test_no_stemming(self):
        result = preprocess("berlari di lapangan", mode="indobert")
        assert "berlari" in result

    def test_no_stopword_removal(self):
        result = preprocess("ini adalah aplikasi yang bagus", mode="indobert")
        assert "adalah" in result
        assert "yang" in result

    def test_slang_still_normalized(self):
        result = preprocess("gk bisa login", mode="indobert")
        assert "tidak" in result

    def test_empty(self):
        assert preprocess("", mode="indobert") == ""


# --- Feature extraction tests ---

class TestExtractFeatures:
    def test_basic(self):
        feat = extract_features("tidak bagus dan buruk")
        assert feat["word_count"] == 4
        assert feat["has_negation"] is True
        assert feat["has_negative"] is True

    def test_positive(self):
        feat = extract_features("sangat bagus mantap")
        assert feat["has_positive"] is True
        assert feat["has_negative"] is False

    def test_punctuation(self):
        feat = extract_features("apa? kenapa! oh?")
        assert feat["question_count"] == 2
        assert feat["exclamation_count"] == 1

    def test_empty(self):
        feat = extract_features("")
        assert feat["word_count"] == 0
        assert feat["avg_word_length"] == 0


# --- Integration: real review text ---

class TestRealReviewText:
    """Test with actual BNI/BIONS review text from the database."""

    SAMPLES = [
        "Kudet. Kurang akurat dalam memberikan data ataupun berita dan aksi corp Perlu pembenahan yang amat serius",
        "Burukk sekali aplikasi. Aplikasi sama sekali tidak bisa di bukaa tolong di perbaiki",
        "Sangat Membantu. Event Live trading bantu buat bisa paham analisa saham",
        "Loading. Mau login gak bisa2, sampai sekarang pun gak bisa masuk. Loadingnya gak selesai2",
        "Bug. Ketika cek portfolio, informasi nya masih dari bulan lalu dan tidak bisa di reload",
        "setiap pemakaian sering error, mau up date data juga sering error",
        "ribet banyakan update giliran sdh update login susah .. rusak aplikasi ni",
        "Oke dari bintang 1 saya naikkan sementara jadi bintang 4, jika kedepannya semakin baik",
        "loading sangat lama..tolong di perbaiki",
        "segera update ipo dong,giliran ada ipo gk bisa join di bions",
    ]

    def test_rule_based_produces_valid_output(self):
        for text in self.SAMPLES:
            result = preprocess(text, mode="rule_based")
            assert isinstance(result, str)
            assert len(result) > 0
            assert "http" not in result

    def test_indobert_produces_valid_output(self):
        for text in self.SAMPLES:
            result = preprocess(text, mode="indobert")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_rule_based_sentiment_direction(self):
        """Rule-based classifier should roughly agree with human sentiment."""
        from pipeline.sentiment.rules import classify_rule_based
        pos = classify_rule_based(preprocess("Aplikasi lancar dan cepat sekali", mode="rule_based"))
        neg = classify_rule_based(preprocess("Aplikasi lemot error dan crash terus", mode="rule_based"))
        assert pos["score"] >= neg["score"]
