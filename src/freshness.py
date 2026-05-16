from datetime import datetime, timedelta, timezone


def get_freshness_settings(config):
    max_news_age_hours = int(config.get("max_news_age_hours", 48))
    initial_backfill_enabled = bool(config.get("initial_backfill_enabled", False))
    initial_backfill_days = int(config.get("initial_backfill_days", 7))
    future_tolerance_hours = int(config.get("future_tolerance_hours", 6))

    active_hours = max_news_age_hours
    if initial_backfill_enabled:
        active_hours = initial_backfill_days * 24

    return {
        "max_news_age_hours": max_news_age_hours,
        "initial_backfill_enabled": initial_backfill_enabled,
        "initial_backfill_days": initial_backfill_days,
        "future_tolerance_hours": future_tolerance_hours,
        "active_hours": active_hours,
    }


def evaluate_freshness(published_date, settings, now=None):
    now = normalize_now(now)
    active_hours = settings.get("active_hours", 48)
    future_tolerance_hours = settings.get("future_tolerance_hours", 6)

    if not published_date:
        return {
            "status": "missing",
            "include_in_report": True,
            "reason": "fecha de publicación no clara",
        }

    parsed_date = parse_publication_datetime(published_date)
    if parsed_date is None:
        return {
            "status": "malformed",
            "include_in_report": False,
            "reason": "fecha de publicación mal parseada",
        }

    if parsed_date > now + timedelta(hours=future_tolerance_hours):
        return {
            "status": "future",
            "include_in_report": False,
            "reason": "fecha futura absurda",
        }

    oldest_allowed = now - timedelta(hours=active_hours)
    if parsed_date < oldest_allowed:
        return {
            "status": "old",
            "include_in_report": False,
            "reason": "noticia antigua",
        }

    return {
        "status": "recent",
        "include_in_report": True,
        "reason": "",
    }


def parse_publication_datetime(value):
    value = (value or "").strip()
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    known_formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]

    for date_format in known_formats:
        try:
            parsed = datetime.strptime(normalized, date_format)
            return ensure_timezone(parsed)
        except ValueError:
            continue

    try:
        return ensure_timezone(datetime.fromisoformat(normalized))
    except ValueError:
        return None


def ensure_timezone(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_now(now):
    if now is None:
        return datetime.now(timezone.utc)
    return ensure_timezone(now)


def freshness_report_text(settings):
    if settings.get("initial_backfill_enabled"):
        days = settings.get("initial_backfill_days", 7)
        return f"Noticias analizadas publicadas en los últimos {days} días"
    hours = settings.get("max_news_age_hours", 48)
    return f"Noticias analizadas publicadas en las últimas {hours} horas"
