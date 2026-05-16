from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import sleep
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def fetch_all_items(config):
    google_config = config.get("google_news", {})
    additional_rss = config.get("additional_rss", [])
    query_groups = config.get("queries", [])
    temporal_filter = get_google_news_temporal_filter(config)
    items = []

    if google_config.get("enabled", True):
        for group in query_groups:
            sector = group.get("sector", "Sin sector")
            for query in group.get("terms", []):
                filtered_query = add_temporal_filter_to_query(query, temporal_filter)
                url = build_google_news_url(filtered_query, google_config)
                print(f"Buscando en RSS: {sector} | {filtered_query}")
                items.extend(fetch_rss_url(url, sector, query, google_config))
                sleep(float(google_config.get("pause_seconds", 1)))

    for source in additional_rss:
        if not source.get("enabled", True):
            continue
        print(f"Consultando fuente RSS adicional: {source.get('name', 'RSS')}")
        items.extend(
            fetch_rss_url(
                source.get("url", ""),
                source.get("sector", "General"),
                source.get("name", "RSS adicional"),
                google_config,
            )
        )

    return items


def get_google_news_temporal_filter(config):
    if config.get("initial_backfill_enabled", False):
        days = int(config.get("initial_backfill_days", 7))
        return f"when:{days}d"

    max_news_age_hours = int(config.get("max_news_age_hours", 48))
    if max_news_age_hours <= 48:
        return "when:2d"
    if max_news_age_hours <= 72:
        return "when:3d"

    days = max(1, (max_news_age_hours + 23) // 24)
    return f"when:{days}d"


def add_temporal_filter_to_query(query, temporal_filter):
    if not temporal_filter or "when:" in query.lower():
        return query
    return f"{query} {temporal_filter}"


def build_google_news_url(query, google_config):
    language = google_config.get("language", "es")
    country = google_config.get("country", "ES")
    encoded_query = quote_plus(query)
    return (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"
    )


def fetch_rss_url(url, sector, query, google_config):
    if not url:
        return []

    timeout = int(google_config.get("timeout_seconds", 15))
    max_results = int(google_config.get("max_results_per_query", 10))

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "private-project-finder/1.0 (+local daily RSS reader)"
            },
        )
        with urlopen(request, timeout=timeout) as response:
            raw_xml = response.read()
    except Exception as exc:
        print(f"  Aviso: no se pudo consultar la fuente RSS: {exc}")
        return []

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        print(f"  Aviso: la respuesta RSS no se pudo interpretar: {exc}")
        return []

    entries = parse_rss_entries(root)
    parsed_items = []

    for entry in entries[:max_results]:
        parsed_items.append(
            {
                "sector": sector,
                "query": query,
                "source": entry.get("source") or entry.get("feed_title") or "RSS",
                "source_url": entry.get("source_url", ""),
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", "").strip(),
                "published_date": normalize_date(entry.get("published_date", "")),
                "summary": entry.get("summary", "").strip(),
            }
        )

    return parsed_items


def parse_rss_entries(root):
    channel = root.find("channel")
    feed_title = ""
    if channel is not None:
        feed_title = get_child_text(channel, "title")
        items = channel.findall("item")
    else:
        feed_title = get_child_text(root, "title")
        items = find_atom_entries(root)

    entries = []
    for item in items:
        entries.append(
            {
                "feed_title": feed_title,
                "title": get_child_text(item, "title"),
                "link": get_link(item),
                "published_date": (
                    get_child_text(item, "pubDate")
                    or get_child_text(item, "published")
                    or get_child_text(item, "updated")
                ),
                "summary": get_child_text(item, "description")
                or get_child_text(item, "summary"),
                "source": get_child_text(item, "source"),
                "source_url": get_child_attribute(item, "source", "url"),
            }
        )
    return entries


def find_atom_entries(root):
    entries = []
    for element in root.iter():
        if strip_namespace(element.tag) == "entry":
            entries.append(element)
    return entries


def get_child_text(parent, child_name):
    for child in list(parent):
        if strip_namespace(child.tag) == child_name:
            return child.text or ""
    return ""


def get_child_attribute(parent, child_name, attribute_name):
    for child in list(parent):
        if strip_namespace(child.tag) == child_name:
            return child.attrib.get(attribute_name, "")
    return ""


def get_link(item):
    direct_link = get_child_text(item, "link")
    if direct_link:
        return direct_link

    for child in list(item):
        if strip_namespace(child.tag) == "link":
            return child.attrib.get("href", "")
    return ""


def strip_namespace(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def normalize_date(raw_date):
    if not raw_date:
        return ""

    try:
        parsed_date = parsedate_to_datetime(raw_date)
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        pass

    known_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for date_format in known_formats:
        try:
            parsed_date = datetime.strptime(raw_date, date_format)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue

    return raw_date
