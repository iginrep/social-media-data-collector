from pipeline.sentiment.classifier import classify


def test_classify_positive():
    result = classify("BIONS sekarang lancar dan cepat")
    assert result["label"] == "positive"
    assert result["score"] > 0


def test_classify_negative():
    result = classify("BIONS error login gagal order nyangkut")
    assert result["label"] == "negative"
    assert result["score"] < 0


def test_classify_neutral():
    result = classify("berapa fee bni sekuritas")
    assert result["label"] == "neutral"
    assert result["score"] == 0
