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
    normalize_word_elongation,
    # stopwords
    remove_stopwords,
    # stemming
    stem_indonesian,
    # full pipeline
    preprocess,
    # features
    extract_features,
    # config loaders
    _get_sentiment_keepers,
    _get_domain_normalization,
)

pytestmark = pytest.mark.unit


# --- Cleaning tests ---

class TestRemoveUrls:
    def test_http(self):
        assert normalize_whitespace(remove_urls("check https://example.com now")) == "check now"

    def test_www(self):
        assert normalize_whitespace(remove_urls("visit www.test.com today")) == "visit today"

    def test_no_url(self):
        assert remove_urls("hello world") == "hello world"


class TestRemoveHtml:
    def test_basic(self):
        assert normalize_whitespace(remove_html("<p>Hello</p> <b>World</b>")) == "Hello World"

    def test_no_html(self):
        assert remove_html("plain text") == "plain text"


class TestRemoveEmojis:
    def test_emoji(self):
        text = "bagus 👍 very good"
        result = remove_emojis(text)
        assert "👍" not in result
        assert "bagus" in result

    def test_no_emoji(self):
        assert remove_emojis("no emojis here") == "no emojis here"


class TestRemoveMentions:
    def test_mention(self):
        assert normalize_whitespace(remove_mentions("hi @user thanks")) == "hi thanks"

    def test_no_mention(self):
        assert remove_mentions("no mentions") == "no mentions"


class TestHashtags:
    def test_extract(self):
        assert extract_hashtags("trending #nlp and #ai") == ["nlp", "ai"]

    def test_strip_symbol(self):
        assert remove_hashtag_symbol("trending #nlp and #ai") == "trending nlp and ai"


class TestNormalizeRepeatedChars:
    def test_triple(self):
        assert normalize_repeated_chars("bagusss") == "baguss"

    def test_quad(self):
        assert normalize_repeated_chars("okkkk") == "okk"

    def test_double_unchanged(self):
        assert normalize_repeated_chars("okk") == "okk"

    def test_empty(self):
        assert normalize_repeated_chars("") == ""


class TestRemoveNumbers:
    def test_numbers(self):
        assert normalize_whitespace(remove_numbers("rating 5 bintang")) == "rating bintang"

    def test_no_numbers(self):
        assert remove_numbers("no numbers") == "no numbers"


class TestRemoveSpecialChars:
    def test_special(self):
        assert normalize_whitespace(remove_special_chars("hello! how are you? fine.")) == "hello how are you fine"

    def test_keep_alnum(self):
        assert remove_special_chars("abc123") == "abc123"


class TestRemoveAccents:
    def test_accented(self):
        assert remove_accents("café résumé") == "cafe resume"

    def test_no_accent(self):
        assert remove_accents("plain") == "plain"


class TestNormalizeWhitespace:
    def test_multi_space(self):
        assert normalize_whitespace("hello   world  ") == "hello world"

    def test_tabs_newlines(self):
        assert normalize_whitespace("hello\tworld\n") == "hello world"


# --- Normalization tests (library-backed) ---

class TestNormalizeSlang:
    def test_gk_to_enggak(self):
        """indoNLP normalizes gk → enggak (not tidak)."""
        result = normalize_slang("gk bisa")
        assert "enggak" in result.split()

    def test_yg_to_yang(self):
        result = normalize_slang("yg bagus")
        assert "yang" in result.split()

    def test_passthrough(self):
        result = normalize_slang("aplikasi bagus")
        assert "aplikasi" in result.split()

    def test_domain_specific(self):
        """Domain terms from domain.json should normalize."""
        result = normalize_slang("error crash bug lemot")
        assert "galat" in result.split()
        assert "macet" in result.split()


class TestNormalizeWordElongation:
    def test_triple_char(self):
        result = normalize_word_elongation("baguuuus")
        assert "bagus" in result.lower()

    def test_no_elongation(self):
        result = normalize_word_elongation("bagus")
        assert "bagus" in result.lower()


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


# --- Config tests ---

class TestDomainConfig:
    def test_sentiment_keepers_not_empty(self):
        keepers = _get_sentiment_keepers()
        assert len(keepers) > 20
        assert "tidak" in keepers
        assert "bagus" in keepers
        assert "buruk" in keepers

    def test_domain_normalization_not_empty(self):
        domain = _get_domain_normalization()
        assert len(domain) > 10
        assert "lemot" in domain
        assert domain["lemot"] == "lambat"


# --- Stemming tests ---

class TestStemIndonesian:
    def test_basic(self):
        result = stem_indonesian("berlari")
        assert "lari" in result

    def test_meng(self):
        result = stem_indonesian("membaca")
        assert "baca" in result


# --- Full pipeline tests ---

class TestPreprocessRuleBased:
    def test_basic(self):
        result = preprocess("Ini aplikasi yang bagus", mode="rule_based")
        assert "aplikasi" in result
        assert "bagus" in result

    def test_empty(self):
        assert preprocess("", mode="rule_based") == ""

    def test_stopwords_removed(self):
        result = preprocess("ini adalah aplikasi yang sangat bagus", mode="rule_based")
        words = result.split()
        assert "adalah" not in words
        assert "yang" not in words

    def test_slang_normalized(self):
        result = preprocess("gk bisa login", mode="rule_based")
        words = result.split()
        assert "enggak" in words

    def test_stemming_applied(self):
        result = preprocess("berlari ke sana", mode="rule_based")
        assert "lari" in result


class TestPreprocessIndobert:
    def test_no_stemming(self):
        result = preprocess("berlari ke sana", mode="indobert")
        # no stemming in indobert mode
        assert "berlari" in result

    def test_slang_normalized(self):
        result = preprocess("gk bisa", mode="indobert")
        assert "enggak" in result

    def test_empty(self):
        assert preprocess("", mode="indobert") == ""


# --- Feature extraction tests ---

class TestExtractFeatures:
    def test_basic(self):
        features = extract_features("aplikasi bagus dan cepat")
        assert features["word_count"] == 4
        assert features["has_positive"] is True

    def test_negation(self):
        features = extract_features("tidak bagus")
        assert features["has_negation"] is True

    def test_empty(self):
        features = extract_features("")
        assert features["word_count"] == 0
