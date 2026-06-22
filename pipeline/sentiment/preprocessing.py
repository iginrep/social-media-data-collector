from __future__ import annotations

"""
Comprehensive Indonesian text preprocessing for BNI/BIONS sentiment analysis.

Two modes:
  - rule_based: full pipeline (clean → normalize → stopwords → stemming)
  - indobert: lighter pipeline (clean → normalize → tokenizer handles the rest)

Libraries used (no hardcoded lists):
  - indoNLP: slang normalization (3300+ entries), word elongation, HTML/URL removal
  - NLTK: Indonesian stopword list (758 words, corpus-based)
  - Sastrawi: Indonesian stemmer (rule-based suffix/prefix stripping)

Domain-specific normalization loaded from domain.json (app/trading terms).
Sentiment keepers also loaded from domain.json.
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# 1. CONFIGURATION (loaded from domain.json — no hardcodes)
# ---------------------------------------------------------------------------

_DOMAIN_CONFIG: dict | None = None
_DOMAIN_DIR = Path(__file__).parent


def _load_domain_config() -> dict:
    """Load domain configuration from domain.json. Cached after first call."""
    global _DOMAIN_CONFIG
    if _DOMAIN_CONFIG is not None:
        return _DOMAIN_CONFIG
    config_path = _DOMAIN_DIR / "domain.json"
    with open(config_path, encoding="utf-8") as f:
        _DOMAIN_CONFIG = json.load(f)
    return _DOMAIN_CONFIG


def _get_domain_normalization() -> dict[str, str]:
    """App/trading-specific term normalization (e.g., lemot → lambat)."""
    return _load_domain_config()["domain_normalization"]


def _get_sentiment_keepers() -> set[str]:
    """Sentiment-bearing words to preserve from stopword removal."""
    return set(_load_domain_config()["sentiment_keepers"])


# ---------------------------------------------------------------------------
# 2. CLEANING (standard regex patterns — no library covers all 5)
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "]+",
    flags=re.UNICODE,
)
_MENTION_RE = re.compile(r"@\w+")
_HASH_RE = re.compile(r"#(\w+)")
_MULTI_SPACE_RE = re.compile(r"\s+")
_NON_ALPHA_RE = re.compile(r"[^a-z0-9\s]")
_NUMBER_RE = re.compile(r"\b\d+\b")


def remove_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)


def remove_html(text: str) -> str:
    return _HTML_RE.sub(" ", text)


def remove_emojis(text: str) -> str:
    return _EMOJI_RE.sub(" ", text)


def remove_mentions(text: str) -> str:
    return _MENTION_RE.sub(" ", text)


def extract_hashtags(text: str) -> list[str]:
    """Extract hashtags before stripping the # symbol."""
    return _HASH_RE.findall(text)


def remove_hashtag_symbol(text: str) -> str:
    """Keep the word, drop the #."""
    return _HASH_RE.sub(r"\1", text)


def normalize_repeated_chars(text: str) -> str:
    """Reduce character repeats: 'bagusss' → 'bagus', 'loadingg' → 'loading'.

    Strategy: collapse any run of 3+ identical chars to 2.
    """
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def remove_numbers(text: str) -> str:
    return _NUMBER_RE.sub(" ", text)


def remove_special_chars(text: str) -> str:
    """Keep only lowercase letters, digits, and whitespace."""
    return _NON_ALPHA_RE.sub(" ", text)


def normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def remove_accents(text: str) -> str:
    """NFD decomposition → strip combining marks. 'é' → 'e'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# 3. NORMALIZATION (library-backed + domain config)
# ---------------------------------------------------------------------------

def normalize_slang(text: str) -> str:
    """Map informal/slang words to formal Indonesian.

    Uses indoNLP's replace_slang() for 3300+ generic entries,
    then applies domain.json overrides for app/trading terms.
    """
    from indoNLP.preprocessing import replace_slang as _indo_slang

    # indoNLP works on original case, we lowercase after
    text = _indo_slang(text)
    text = text.lower()

    # domain-specific overrides (app/trading terms not in indoNLP)
    domain_map = _get_domain_normalization()
    words = text.split()
    return " ".join(domain_map.get(w, w) for w in words)


def normalize_word_elongation(text: str) -> str:
    """Fix word elongation using indoNLP + regex fallback.

    indoNLP handles: 'okkkk' → 'ok', 'burukk' → 'buruk', 'bukaa' → 'buka'
    Regex fallback: 'baguuuus' → 'bagus' (collapse all repeated chars to single)
    """
    from indoNLP.preprocessing import replace_word_elongation as _indo_elong

    text = _indo_elong(text)
    # regex fallback: collapse any run of 2+ identical chars to 1
    text = re.sub(r"(.)\1+", r"\1", text)
    return text


def normalize_unicode(text: str) -> str:
    """NFC normalize to standard form."""
    return unicodedata.normalize("NFC", text)


# ---------------------------------------------------------------------------
# 4. STOPWORD REMOVAL (NLTK-backed)
# ---------------------------------------------------------------------------

_nltk_stopwords: set[str] | None = None


def _get_stopwords() -> set[str]:
    """Load Indonesian stopwords from NLTK corpus. Cached after first call.

    Falls back to Sastrawi's stopword list if NLTK is unavailable.
    """
    global _nltk_stopwords
    if _nltk_stopwords is not None:
        return _nltk_stopwords

    try:
        import nltk
        nltk.download("stopwords", quiet=True)
        from nltk.corpus import stopwords
        _nltk_stopwords = set(stopwords.words("indonesian"))
    except Exception:
        # Fallback: Sastrawi stopword list
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        _nltk_stopwords = set(StopWordRemoverFactory().get_stop_words())

    return _nltk_stopwords


def remove_stopwords(text: str, extra_keep: set[str] | None = None) -> str:
    """Remove Indonesian stopwords (NLTK corpus), keeping sentiment-bearing words."""
    stopwords = _get_stopwords()
    keep = _get_sentiment_keepers() | (extra_keep or set())
    words = text.split()
    return " ".join(w for w in words if w in keep or w not in stopwords)


# ---------------------------------------------------------------------------
# 5. STEMMING (Sastrawi)
# ---------------------------------------------------------------------------

_stemmer = None


def _get_stemmer():
    global _stemmer
    if _stemmer is None:
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
        _stemmer = StemmerFactory().create_stemmer()
    return _stemmer


def stem_indonesian(text: str) -> str:
    """Stem Indonesian text using Sastrawi. Cached after first call."""
    return _get_stemmer().stem(text)


# ---------------------------------------------------------------------------
# 6. FULL PIPELINES
# ---------------------------------------------------------------------------

PipelineMode = Literal["rule_based", "indobert"]


def preprocess(
    text: str,
    mode: PipelineMode = "rule_based",
    *,
    remove_nums: bool = False,
    do_stemming: bool = True,
    do_stopwords: bool = True,
    extra_keep_words: set[str] | None = None,
) -> str:
    """Full preprocessing pipeline.

    mode="rule_based":  clean → normalize → stopwords (NLTK) → stemming (Sastrawi)
    mode="indobert":    clean → normalize only (tokenizer handles the rest)

    Args:
        text: raw input text
        mode: "rule_based" for classical NLP, "indobert" for transformer input
        remove_nums: whether to strip numbers
        do_stemming: whether to apply Sastrawi stemmer (rule_based only)
        do_stopwords: whether to remove stopwords (rule_based only, NLTK-backed)
        extra_keep_words: additional words to preserve from stopword removal
    """
    if not text or not text.strip():
        return ""

    # --- Stage 1: Cleaning (always) ---
    text = text.lower()
    text = remove_urls(text)
    text = remove_html(text)
    text = remove_emojis(text)
    text = remove_mentions(text)
    text = remove_hashtag_symbol(text)
    text = normalize_unicode(text)
    text = remove_accents(text)
    text = remove_special_chars(text)
    if remove_nums:
        text = remove_numbers(text)
    text = normalize_whitespace(text)

    if not text:
        return ""

    # --- Stage 2: Normalization (library-backed) ---
    # indoNLP: word elongation + slang normalization
    text = normalize_word_elongation(text)
    text = normalize_slang(text)

    # --- Stage 3: Mode-specific ---
    if mode == "indobert":
        # IndoBERT tokenizer handles tokenization, stopwords, subwords.
        # Only cleaning + slang normalization is needed.
        return normalize_whitespace(text)

    # rule_based mode
    if do_stopwords:
        text = remove_stopwords(text, extra_keep=extra_keep_words)
    if do_stemming:
        text = stem_indonesian(text)
    return normalize_whitespace(text)


# ---------------------------------------------------------------------------
# 7. BATCH PREPROCESSING
# ---------------------------------------------------------------------------


def preprocess_batch(
    texts: list[str],
    mode: PipelineMode = "rule_based",
    **kwargs,
) -> list[str]:
    """Preprocess a list of texts. Applies stemmer lazily (once)."""
    return [preprocess(t, mode=mode, **kwargs) for t in texts]


# ---------------------------------------------------------------------------
# 8. FEATURE EXTRACTION (for rule-based / classical models)
# ---------------------------------------------------------------------------


def extract_features(text: str) -> dict:
    """Extract linguistic features from preprocessed text."""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "avg_word_length": sum(len(w) for w in words) / max(len(words), 1),
        "unique_words": len(set(words)),
        "has_negation": bool({"tidak", "bukan", "belum", "jangan", "kurang"} & set(words)),
        "has_positive": bool({"bagus", "mantap", "puas", "lancar", "cepat", "mudah"} & set(words)),
        "has_negative": bool({"buruk", "jelek", "parah", "gagal", "lemot", "susah"} & set(words)),
        "exclamation_count": text.count("!"),
        "question_count": text.count("?"),
        "repeated_char_count": len(re.findall(r"(.)\1", text)),
    }
