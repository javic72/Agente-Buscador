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
