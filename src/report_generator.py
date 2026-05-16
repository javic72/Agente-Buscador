from html import escape
from pathlib import Path


def generate_daily_report(
    opportunities,
    reports_dir,
    report_date,
    temporal_label="",
    summary_stats=None,
    max_discarded_items=25,
):
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"daily_report_{report_date.isoformat()}.html"

    groups = {
        "Alta": [item for item in opportunities if item["priority"] == "Alta"],
        "Media": [item for item in opportunities if item["priority"] == "Media"],
        "Baja": [item for item in opportunities if item["priority"] == "Baja"],
        "Descartada": [
            item for item in opportunities if item["priority"] == "Descartada"
        ],
    }

    html = build_html(
        groups,
        report_date,
        temporal_label,
        summary_stats or {},
        max_discarded_items=max_discarded_items,
    )
    report_path.write_text(html, encoding="utf-8")
    return report_path


def build_html(groups, report_date, temporal_label, summary_stats, max_discarded_items=25):
    total = sum(len(items) for items in groups.values())
    cards = build_summary_cards(summary_stats, groups)
    has_recent_opportunities = bool(groups["Alta"] or groups["Media"] or groups["Baja"])
    no_opportunities_message = ""
    if not has_recent_opportunities:
        no_opportunities_message = (
            '<article class="empty">'
            "No se han detectado oportunidades recientes en el rango temporal configurado."
            "</article>"
        )

    sections = "\n".join(
        [
            build_section("Oportunidades Alta", groups["Alta"]),
            build_section("Oportunidades Media", groups["Media"]),
            build_section("Oportunidades Baja", groups["Baja"]),
            build_section(
                "Descartadas recientes por otros motivos",
                groups["Descartada"][:max_discarded_items],
                hidden_count=max(0, len(groups["Descartada"]) - max_discarded_items),
            ),
        ]
    )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daily report {escape(report_date.isoformat())}</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: #1f2933;
      background: #f5f7fa;
    }}
    header {{
      background: #17202a;
      color: white;
      padding: 28px 36px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px;
    }}
    h1, h2, h3 {{
      margin: 0;
      letter-spacing: 0;
    }}
    h1 {{
      font-size: 28px;
      margin-bottom: 6px;
    }}
    h2 {{
      font-size: 22px;
      margin: 28px 0 14px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin: 20px 0 10px;
    }}
    .summary-card {{
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      padding: 16px;
    }}
    .summary-card strong {{
      display: block;
      font-size: 28px;
      margin-top: 6px;
    }}
    article {{
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 14px;
    }}
    .meta {{
      color: #52616b;
      font-size: 13px;
      margin: 8px 0 12px;
    }}
    .score {{
      display: inline-block;
      min-width: 56px;
      text-align: center;
      border-radius: 999px;
      padding: 4px 10px;
      color: white;
      background: #2563eb;
      font-weight: bold;
    }}
    .Alta .score {{ background: #047857; }}
    .Media .score {{ background: #b45309; }}
    .Baja .score {{ background: #4b5563; }}
    .Descartada .score {{ background: #991b1b; }}
    dl {{
      display: grid;
      grid-template-columns: minmax(140px, 220px) 1fr;
      gap: 8px 12px;
      margin: 12px 0 0;
    }}
    dt {{
      font-weight: bold;
      color: #334e68;
    }}
    dd {{
      margin: 0;
    }}
    a {{
      color: #1d4ed8;
    }}
    .empty {{
      color: #52616b;
      background: transparent;
      border: 1px dashed #bcccdc;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Informe diario de oportunidades privadas</h1>
    <div>{escape(report_date.isoformat())}</div>
  </header>
  <main>
    <h2>Resumen ejecutivo</h2>
    <p><strong>{escape(temporal_label)}</strong></p>
    <p>Noticias listadas en el informe: <strong>{total}</strong>. Las oportunidades se ordenan por señales de proyecto físico privado, prioridad comercial y riesgo de descarte.</p>
    <div class="summary">{cards}</div>
    {no_opportunities_message}
    {sections}
  </main>
</body>
</html>"""


def build_summary_cards(summary_stats, groups):
    if not summary_stats:
        summary_stats = {
            "Noticias encontradas": sum(len(items) for items in groups.values()),
            "Noticias dentro del rango temporal": sum(len(items) for items in groups.values()),
            "Oportunidades altas": len(groups["Alta"]),
            "Oportunidades medias": len(groups["Media"]),
            "Oportunidades bajas": len(groups["Baja"]),
            "Descartadas por antigüedad": 0,
            "Descartadas por otros motivos": len(groups["Descartada"]),
            "Penalizadas por ya inauguradas": 0,
            "Duplicados ocultados en informe": 0,
        }

    labels = [
        "Noticias encontradas",
        "Noticias dentro del rango temporal",
        "Oportunidades altas",
        "Oportunidades medias",
        "Oportunidades bajas",
        "Descartadas por antigüedad",
        "Descartadas por otros motivos",
        "Penalizadas por ya inauguradas",
        "Duplicados ocultados en informe",
    ]
    return "".join(summary_card(label, summary_stats.get(label, 0)) for label in labels)


def summary_card(label, count):
    return f'<div class="summary-card">{escape(label)}<strong>{count}</strong></div>'


def build_section(title, items, hidden_count=0):
    if not items:
        return f"<h2>{escape(title)}</h2><article class=\"empty\">Sin registros en esta sección.</article>"

    articles = [build_article(item) for item in items]
    hidden_note = ""
    if hidden_count:
        hidden_note = (
            f'<article class="empty">Se han ocultado {hidden_count} descartadas '
            "adicionales para mantener el informe legible.</article>"
        )
    return f"<h2>{escape(title)}</h2>{''.join(articles)}{hidden_note}"


def build_article(item):
    priority_class = escape(item.get("priority", ""))
    title = escape(item.get("title", "Sin título"))
    url = escape(item.get("url", ""))
    source = escape(item.get("source", ""))
    sector = escape(item.get("sector", ""))
    published = escape(item.get("published_date", ""))
    score = escape(str(item.get("score", "")))

    return f"""<article class="{priority_class}">
  <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
  <div class="meta">
    <span class="score">{score}</span>
    <span>{sector} | {source} | publicado: {published}</span>
  </div>
  <dl>
    <dt>Proyecto</dt><dd>{escape(item.get("project_type", ""))}</dd>
    <dt>Señal detectada</dt><dd>{escape(item.get("detected_signal", ""))}</dd>
    <dt>fase_detectada</dt><dd>{escape(item.get("fase_detectada", ""))}</dd>
    <dt>timing_reason</dt><dd>{escape(item.get("timing_reason", ""))}</dd>
    <dt>Operador detectado</dt><dd>{escape(item.get("detected_company_or_operator", ""))}</dd>
    <dt>Ciudad o zona</dt><dd>{escape(item.get("city_or_area", ""))}</dd>
    <dt>Resumen</dt><dd>{escape(item.get("summary", ""))}</dd>
    <dt>Necesidades probables</dt><dd>{escape(item.get("probable_technology_needs", ""))}</dd>
    <dt>Motivo</dt><dd>{escape(item.get("priority_reason", ""))}</dd>
    <dt>Acción sugerida</dt><dd>{escape(item.get("suggested_action", ""))}</dd>
  </dl>
</article>"""
