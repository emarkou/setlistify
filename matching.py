import re
import unicodedata


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    # strip common live suffixes
    text = re.sub(r"\b(live|acoustic|demo|version|remaster(?:ed)?|radio edit)\b", "", text)
    return text.strip()


def _token_sort_ratio(a: str, b: str) -> float:
    a_tokens = sorted(_normalize(a).split())
    b_tokens = sorted(_normalize(b).split())
    a_str = " ".join(a_tokens)
    b_str = " ".join(b_tokens)
    if not a_str or not b_str:
        return 0.0
    # simple Jaccard over character bigrams
    def bigrams(s):
        return {s[i:i+2] for i in range(len(s) - 1)}
    bg_a = bigrams(a_str)
    bg_b = bigrams(b_str)
    if not bg_a and not bg_b:
        return 1.0
    intersection = len(bg_a & bg_b)
    union = len(bg_a | bg_b)
    return intersection / union if union else 0.0


def best_match(query: str, candidates: list[dict], threshold: float = 0.5) -> dict | None:
    """
    candidates: list of dicts with at least a 'name' key.
    Returns best candidate above threshold, or None.
    """
    best = None
    best_score = 0.0
    for c in candidates:
        score = _token_sort_ratio(query, c.get("name", ""))
        if score > best_score:
            best_score = score
            best = c
    return best if best_score >= threshold else None
