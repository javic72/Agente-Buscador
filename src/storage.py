import csv
from pathlib import Path


FIELDNAMES = [
    "detected_date",
    "published_date",
    "sector",
    "source",
    "title",
    "url",
    "detected_company_or_operator",
    "city_or_area",
    "project_type",
    "detected_signal",
    "fase_detectada",
    "timing_reason",
    "summary",
    "probable_technology_needs",
    "score",
    "priority",
    "priority_reason",
    "suggested_action",
    "status",
    "notes",
]


def ensure_storage(csv_path):
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
        return

    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        existing_rows = list(reader)
        existing_fieldnames = reader.fieldnames or []

    if all(field in existing_fieldnames for field in FIELDNAMES):
        return

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(row)


def load_history(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return []

    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def append_records(csv_path, records):
    if not records:
        return

    with Path(csv_path).open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, extrasaction="ignore")
        for record in records:
            writer.writerow(record)
