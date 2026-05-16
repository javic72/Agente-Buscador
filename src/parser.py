from datetime import datetime
import html
import re


def build_opportunity(item, keywords_config):
    text = clean_text(f"{item.get('title', '')}. {item.get('summary', '')}")
    project_type, signal = detect_project_type(text, keywords_config)
    city_or_area = detect_city_or_area(text, keywords_config)
    company_or_operator = detect_company_or_operator(text)

    return {
        "detected_date": datetime.now().date().isoformat(),
        "published_date": item.get("published_date", ""),
        "sector": item.get("sector", ""),
        "source": item.get("source", ""),
        "title": clean_text(item.get("title", "")),
        "url": item.get("url", ""),
        "detected_company_or_operator": company_or_operator,
        "city_or_area": city_or_area,
        "project_type": project_type,
        "detected_signal": signal,
        "fase_detectada": "desconocida",
        "timing_reason": "",
        "summary": shorten(text, 420),
        "probable_technology_needs": build_technology_needs(
            item.get("sector", ""), project_type, keywords_config
        ),
        "score": 0,
        "priority": "",
        "priority_reason": "",
        "suggested_action": "",
        "status": "Nuevo",
        "notes": "",
    }


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def shorten(value, max_length):
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def detect_project_type(text, keywords_config):
    normalized = text.lower()
    for group in keywords_config.get("project_type_keywords", []):
        for keyword in group.get("keywords", []):
            if keyword.lower() in normalized:
                return group.get("project_type", "Proyecto físico"), keyword
    return "Proyecto físico por validar", "Sin señal fuerte"


def detect_city_or_area(text, keywords_config):
    cities = keywords_config.get("cities_or_areas", [])
    lower_text = text.lower()
    for city in cities:
        if re.search(rf"\b{re.escape(city.lower())}\b", lower_text):
            return city
    return ""


def detect_company_or_operator(text):
    patterns = [
        r"\b(?:empresa|grupo|cadena|operador|marca|compañía)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9&.,\- ]{2,70})",
        r"\b(?:universidad|colegio|hospital|clínica|gimnasio|hotel)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9&.,\- ]{2,70})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip(" .,-")
            return shorten(value, 80)
    return ""


def build_technology_needs(sector, project_type, keywords_config):
    needs_by_sector = keywords_config.get("probable_technology_needs", {})
    default_needs = needs_by_sector.get(
        "default",
        [
            "pantallas informativas",
            "cartelería digital",
            "audio",
            "conectividad para espacios",
        ],
    )
    needs = needs_by_sector.get(sector, default_needs)

    if "hotel" in project_type.lower():
        needs = needs + ["salas de eventos", "señalización digital"]
    if "oficina" in project_type.lower() or "sede" in project_type.lower():
        needs = needs + ["salas de reunión", "videoconferencia"]
    if "tienda" in project_type.lower() or "retail" in project_type.lower():
        needs = needs + ["experiencia en tienda", "LED"]

    unique_needs = []
    for need in needs:
        if need not in unique_needs:
            unique_needs.append(need)
    return "; ".join(unique_needs)
