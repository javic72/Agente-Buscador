from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import re
import unicodedata


class DuplicateChecker:
    def __init__(self, history, similarity_threshold=0.88):
        self.similarity_threshold = similarity_threshold
        self.seen_urls = set()
        self.seen_titles = []

        for record in history:
            self.register(record.get("url", ""), record.get("title", ""))

    def check(self, url, title):
        normalized_url = normalize_url(url)
        normalized_title = normalize_title(title)

        if normalized_url and normalized_url in self.seen_urls:
            return {"is_duplicate": True, "reason": "URL ya registrada en el histórico"}

        for existing_title in self.seen_titles:
            similarity = SequenceMatcher(None, normalized_title, existing_title).ratio()
            if normalized_title and similarity >= self.similarity_threshold:
                return {
                    "is_duplicate": True,
                    "reason": f"título similar al {similarity:.0%}",
                }

        return {"is_duplicate": False, "reason": ""}

    def register(self, url, title):
        normalized_url = normalize_url(url)
        normalized_title = normalize_title(title)
        if normalized_url:
            self.seen_urls.add(normalized_url)
        if normalized_title:
            self.seen_titles.append(normalized_title)


def normalize_url(url):
    if not url:
        return ""

    parts = urlsplit(url.strip())
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(filtered_query),
            "",
        )
    )


def normalize_title(title):
    title = title or ""
    title = unicodedata.normalize("NFKD", title)
    title = "".join(char for char in title if not unicodedata.combining(char))
    title = title.lower()
    title = re.sub(r"[^a-z0-9áéíóúñü ]+", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


REPORT_TITLE_STOPWORDS = {
    "a",
    "al",
    "ante",
    "con",
    "de",
    "del",
    "desde",
    "el",
    "en",
    "entre",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "su",
    "sus",
    "un",
    "una",
    "y",
}

REPORT_TITLE_TIMING_WORDS = {
    "abre",
    "abrira",
    "abierto",
    "apertura",
    "aperturas",
    "inaugura",
    "inaugurada",
    "inaugurado",
    "inaugurar",
    "inauguro",
    "prepara",
    "preve",
    "prevista",
    "previsto",
    "proxima",
    "proximo",
}


def deduplicate_for_report(
    items,
    similarity_threshold=0.9,
    token_overlap_threshold=0.7,
):
    unique_items = []
    duplicate_count = 0

    for item in items:
        duplicate_index = find_report_duplicate(
            unique_items,
            item,
            similarity_threshold,
            token_overlap_threshold,
        )
        if duplicate_index is None:
            unique_items.append(item)
            continue

        duplicate_count += 1
        if should_replace_item(unique_items[duplicate_index], item):
            unique_items[duplicate_index] = item

    return unique_items, duplicate_count


def find_report_duplicate(
    unique_items,
    candidate,
    similarity_threshold,
    token_overlap_threshold,
):
    candidate_url = normalize_canonical_url(candidate.get("url", ""))
    candidate_title = normalize_title(candidate.get("title", ""))

    for index, existing in enumerate(unique_items):
        existing_url = normalize_canonical_url(existing.get("url", ""))
        if candidate_url and existing_url and candidate_url == existing_url:
            return index

        existing_title = normalize_title(existing.get("title", ""))
        if not candidate_title or not existing_title:
            continue
        if candidate_title == existing_title:
            return index
        similarity = SequenceMatcher(None, candidate_title, existing_title).ratio()
        if similarity >= similarity_threshold:
            return index
        if are_title_signatures_similar(
            candidate_title,
            existing_title,
            token_overlap_threshold,
        ):
            return index

    return None


def normalize_canonical_url(url):
    normalized = normalize_url(url)
    parts = urlsplit(normalized)
    if "news.google.com" in parts.netloc and parts.path:
        return parts.path
    return normalized


def are_title_signatures_similar(candidate_title, existing_title, token_overlap_threshold):
    candidate_tokens = title_signature_tokens(candidate_title)
    existing_tokens = title_signature_tokens(existing_title)
    if len(candidate_tokens) < 4 or len(existing_tokens) < 4:
        return False

    common_tokens = candidate_tokens & existing_tokens
    if len(common_tokens) < 4:
        return False

    smaller_signature_size = min(len(candidate_tokens), len(existing_tokens))
    overlap = len(common_tokens) / smaller_signature_size
    return overlap >= token_overlap_threshold


def title_signature_tokens(title):
    tokens = set(title.split())
    return {
        token
        for token in tokens
        if len(token) > 2
        and token not in REPORT_TITLE_STOPWORDS
        and token not in REPORT_TITLE_TIMING_WORDS
    }


def should_replace_item(existing, candidate):
    existing_rank = report_priority_rank(existing)
    candidate_rank = report_priority_rank(candidate)
    if candidate_rank != existing_rank:
        return candidate_rank > existing_rank
    return int(candidate.get("score") or 0) > int(existing.get("score") or 0)


def report_priority_rank(item):
    priority_rank = {
        "Descartada": 0,
        "Baja": 1,
        "Media": 2,
        "Alta": 3,
    }
    return priority_rank.get(item.get("priority", "Descartada"), 0)
