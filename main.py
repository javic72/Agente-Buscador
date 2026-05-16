from pathlib import Path
from datetime import datetime

from src.classifier import classify_opportunity
from src.config_loader import load_yaml
from src.deduplicator import DuplicateChecker, deduplicate_for_report
from src.email_sender import send_daily_email
from src.fetchers import fetch_all_items
from src.freshness import (
    evaluate_freshness,
    freshness_report_text,
    get_freshness_settings,
)
from src.parser import build_opportunity
from src.report_generator import generate_daily_report
from src.source_catalog import update_source_catalog
from src.storage import append_records, ensure_storage, load_history


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
DATA_PATH = BASE_DIR / "data" / "opportunities.csv"
SOURCE_CATALOG_PATH = BASE_DIR / "data" / "sources_catalog.xlsx"
REPORTS_DIR = BASE_DIR / "reports"


def main():
    print("Iniciando buscador diario de oportunidades privadas...")

    sources_config = load_yaml(CONFIG_DIR / "sources.yaml")
    keywords_config = load_yaml(CONFIG_DIR / "keywords.yaml")
    scoring_config = load_yaml(CONFIG_DIR / "scoring.yaml")
    email_config = load_yaml(CONFIG_DIR / "email.yaml")
    freshness_settings = get_freshness_settings(sources_config)
    temporal_label = freshness_report_text(freshness_settings)

    ensure_storage(DATA_PATH)
    history = load_history(DATA_PATH)
    duplicate_checker = DuplicateChecker(
        history,
        similarity_threshold=scoring_config.get("deduplication", {}).get(
            "title_similarity_threshold", 0.88
        ),
    )

    fetched_items = fetch_all_items(sources_config)
    print(f"Noticias encontradas antes de filtrar: {len(fetched_items)}")

    detected_today = []
    report_items = []
    records_to_store = []
    old_news_count = 0
    within_temporal_range_count = 0
    already_opened_penalty_count = 0

    for item in fetched_items:
        duplicate_result = duplicate_checker.check(item.get("url", ""), item.get("title", ""))
        freshness_result = evaluate_freshness(
            item.get("published_date", ""),
            freshness_settings,
        )
        if freshness_result.get("status") == "old":
            old_news_count += 1
        if freshness_result.get("status") == "recent":
            within_temporal_range_count += 1

        opportunity = build_opportunity(item, keywords_config)
        classified = classify_opportunity(
            opportunity,
            scoring_config,
            keywords_config,
            duplicate_result=duplicate_result,
            freshness_result=freshness_result,
        )
        detected_today.append(classified)
        if "ya inaugurado / ya abierto" in classified.get("priority_reason", ""):
            already_opened_penalty_count += 1

        if freshness_result.get("include_in_report", True):
            report_items.append(classified)

        if not duplicate_result["is_duplicate"]:
            records_to_store.append(classified)
            duplicate_checker.register(classified.get("url", ""), classified.get("title", ""))

    append_records(DATA_PATH, records_to_store)
    source_catalog_path = update_source_catalog(SOURCE_CATALOG_PATH, detected_today)

    report_items, report_duplicate_count = deduplicate_for_report(
        report_items,
        similarity_threshold=scoring_config.get("deduplication", {}).get(
            "report_title_similarity_threshold", 0.9
        ),
        token_overlap_threshold=scoring_config.get("deduplication", {}).get(
            "report_title_token_overlap_threshold", 0.7
        ),
    )

    report_counts = {
        "Alta": sum(1 for item in report_items if item["priority"] == "Alta"),
        "Media": sum(1 for item in report_items if item["priority"] == "Media"),
        "Baja": sum(1 for item in report_items if item["priority"] == "Baja"),
        "Descartada": sum(
            1 for item in report_items if item["priority"] == "Descartada"
        ),
    }
    summary_stats = {
        "Noticias encontradas": len(fetched_items),
        "Noticias dentro del rango temporal": within_temporal_range_count,
        "Oportunidades altas": report_counts["Alta"],
        "Oportunidades medias": report_counts["Media"],
        "Oportunidades bajas": report_counts["Baja"],
        "Descartadas por antigüedad": old_news_count,
        "Descartadas por otros motivos": sum(
            1
            for item in report_items
            if item["priority"] == "Descartada" and item.get("notes") != "noticia antigua"
        ),
        "Penalizadas por ya inauguradas": already_opened_penalty_count,
        "Duplicados ocultados en informe": report_duplicate_count,
    }

    report_path = generate_daily_report(
        report_items,
        REPORTS_DIR,
        report_date=datetime.now().date(),
        temporal_label=temporal_label,
        summary_stats=summary_stats,
        max_discarded_items=scoring_config.get("reporting", {}).get(
            "max_discarded_items_in_html", 25
        ),
    )
    email_result = send_daily_email(email_config, report_path, summary_stats)

    print("\nResumen final")
    print(f"- Noticias encontradas: {len(fetched_items)}")
    print(f"- Noticias dentro del rango temporal: {within_temporal_range_count}")
    print(f"- Oportunidades altas: {report_counts['Alta']}")
    print(f"- Oportunidades medias: {report_counts['Media']}")
    print(f"- Oportunidades bajas: {report_counts['Baja']}")
    print(f"- Descartadas por antigüedad: {old_news_count}")
    print(f"- Descartadas por otros motivos: {summary_stats['Descartadas por otros motivos']}")
    print(f"- Penalizadas por ya inauguradas: {already_opened_penalty_count}")
    print(f"- Duplicados ocultados en informe: {report_duplicate_count}")
    print(f"- Informe HTML generado: {report_path}")
    print(f"- Catálogo de fuentes actualizado: {source_catalog_path}")
    if email_result["sent"]:
        print("- Email enviado correctamente")
    else:
        print(f"- Email no enviado: {email_result['reason']}")


if __name__ == "__main__":
    main()
