import unicodedata


def classify_opportunity(
    opportunity,
    scoring_config,
    keywords_config,
    duplicate_result=None,
    freshness_result=None,
):
    duplicate_result = duplicate_result or {"is_duplicate": False, "reason": ""}
    freshness_result = freshness_result or {"status": "recent", "reason": ""}
    text = f"{opportunity.get('title', '')} {opportunity.get('summary', '')}".lower()
    timing_result = detect_timing_phase(text, scoring_config, keywords_config)
    score = 0
    reasons = []

    if freshness_result.get("status") in ("old", "malformed", "future"):
        score = 0
        reasons.append(freshness_result.get("reason", "noticia fuera del rango temporal"))
    elif duplicate_result.get("is_duplicate"):
        score += scoring_config["negative_points"].get("duplicado", -100)
        reasons.append(f"Duplicado: {duplicate_result.get('reason', 'coincidencia previa')}")
    else:
        positive_score, positive_reasons = score_positive_signals(
            text, opportunity, scoring_config, keywords_config
        )
        negative_score, negative_reasons = score_negative_signals(
            text, scoring_config, keywords_config
        )
        score += positive_score + negative_score + timing_result["score"]
        reasons.extend(positive_reasons + negative_reasons + timing_result["reasons"])

        if freshness_result.get("status") == "missing":
            points = scoring_config.get("negative_points", {}).get(
                "fecha_publicacion_no_clara", -15
            )
            score += points
            reasons.append(f"fecha de publicación no clara: {points}")

    score = max(0, min(100, score))
    if freshness_result.get("status") == "missing" and score >= 75:
        score = 74
        reasons.append("sin fecha clara no puede ser prioridad Alta")
    if timing_result["cap_priority_to_baja"] and score >= 50:
        score = 49
        reasons.append("ya inaugurado sin fase futura adicional: prioridad máxima Baja")

    priority = classify_priority(score, scoring_config)

    opportunity["score"] = score
    opportunity["priority"] = priority
    opportunity["fase_detectada"] = timing_result["phase"]
    opportunity["timing_reason"] = timing_result["timing_reason"]
    opportunity["priority_reason"] = "; ".join(reasons) if reasons else "Sin señales suficientes"
    opportunity["suggested_action"] = suggested_action(priority)
    opportunity["status"] = "Descartado" if priority == "Descartada" else "Pendiente de revisión"
    if duplicate_result.get("is_duplicate"):
        opportunity["notes"] = duplicate_result.get("reason", "")
    if freshness_result.get("status") in ("old", "malformed", "future", "missing"):
        opportunity["notes"] = freshness_result.get("reason", opportunity.get("notes", ""))

    return opportunity


def detect_timing_phase(text, scoring_config, keywords_config):
    positive_points = scoring_config.get("positive_points", {})
    negative_points = scoring_config.get("negative_points", {})

    future_hits = find_keyword_hits(text, keywords_config.get("future_project_signals", []))
    planning_hits = find_keyword_hits(text, keywords_config.get("planning_signals", []))
    construction_hits = find_keyword_hits(
        text, keywords_config.get("construction_reform_signals", [])
    )
    upcoming_hits = find_keyword_hits(text, keywords_config.get("upcoming_opening_signals", []))
    expansion_hits = find_keyword_hits(
        text, keywords_config.get("expansion_future_signals", [])
    )
    already_opened_hits = find_keyword_hits(
        text, keywords_config.get("already_opened_signals", [])
    )

    score = 0
    reasons = []

    if future_hits:
        points = positive_points.get("senal_futura_clara", 25)
        score += points
        reasons.append(f"señal futura clara: +{points}")
    if construction_hits:
        points = positive_points.get("en_obra_o_reforma", 20)
        score += points
        reasons.append(f"en obra o reforma: +{points}")
    if upcoming_hits:
        points = positive_points.get("proxima_apertura_futura", 20)
        score += points
        reasons.append(f"próxima apertura futura: +{points}")
    if expansion_hits:
        points = positive_points.get("plan_expansion_futuras_ubicaciones", 15)
        score += points
        reasons.append(f"plan de expansión con futuras ubicaciones: +{points}")
    if already_opened_hits:
        points = negative_points.get("ya_inaugurado_abierto", -60)
        score += points
        reasons.append(f"ya inaugurado / ya abierto: {points}")

    phase = "desconocida"
    timing_reasons = []
    has_future_additional = bool(
        future_hits or planning_hits or construction_hits or upcoming_hits or expansion_hits
    )

    if already_opened_hits and not has_future_additional:
        phase = "ya inaugurado"
        timing_reasons.append(
            "Se detectan señales de proyecto ya inaugurado o ya abierto: "
            + ", ".join(already_opened_hits[:3])
        )
    elif construction_hits:
        phase = "en obra/reforma"
        timing_reasons.append(
            "Se detectan señales de obra, construcción o reforma: "
            + ", ".join(construction_hits[:3])
        )
    elif upcoming_hits:
        phase = "próxima apertura"
        timing_reasons.append(
            "Se detectan señales de apertura futura: " + ", ".join(upcoming_hits[:3])
        )
    elif planning_hits:
        phase = "en planificación"
        timing_reasons.append(
            "Se detectan señales de planificación o búsqueda: "
            + ", ".join(planning_hits[:3])
        )
    elif future_hits:
        phase = "futuro"
        timing_reasons.append(
            "Se detectan señales de proyecto futuro: " + ", ".join(future_hits[:3])
        )
    elif expansion_hits:
        phase = "futuro"
        timing_reasons.append(
            "Se detectan señales de expansión futura: " + ", ".join(expansion_hits[:3])
        )
    elif already_opened_hits:
        phase = "ya inaugurado"
        timing_reasons.append(
            "Se detectan señales de proyecto ya inaugurado o ya abierto: "
            + ", ".join(already_opened_hits[:3])
        )

    if already_opened_hits and has_future_additional:
        timing_reasons.append(
            "También hay señales de proyecto ya inaugurado o ya abierto, por eso se aplica penalización."
        )

    return {
        "phase": phase,
        "timing_reason": " ".join(timing_reasons) if timing_reasons else "Sin fase clara",
        "score": score,
        "reasons": reasons,
        "cap_priority_to_baja": bool(already_opened_hits and not has_future_additional),
        "already_opened_penalty": bool(already_opened_hits),
    }


def find_keyword_hits(text, keywords):
    hits = []
    normalized_text = normalize_for_matching(text)
    for keyword in keywords:
        normalized_keyword = keyword.lower()
        comparable_keyword = normalize_for_matching(normalized_keyword)
        if comparable_keyword in normalized_text and normalized_keyword not in hits:
            hits.append(normalized_keyword)
    return hits


def normalize_for_matching(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.lower()


def score_positive_signals(text, opportunity, scoring_config, keywords_config):
    score = 0
    reasons = []
    positive_points = scoring_config.get("positive_points", {})

    for rule in keywords_config.get("positive_signal_keywords", []):
        label = rule.get("label", "")
        point_key = rule.get("score_key", label)
        for keyword in rule.get("keywords", []):
            if keyword.lower() in text:
                points = positive_points.get(point_key, 0)
                score += points
                reasons.append(f"{label}: +{points}")
                break

    if opportunity.get("city_or_area"):
        points = positive_points.get("ubicacion_concreta", 0)
        score += points
        reasons.append(f"ubicación concreta: +{points}")

    if has_expected_date(text):
        points = positive_points.get("fecha_prevista", 0)
        score += points
        reasons.append(f"fecha prevista: +{points}")

    if has_investment(text):
        points = positive_points.get("inversion_economica", 0)
        score += points
        reasons.append(f"inversión económica: +{points}")

    if has_surface(text):
        points = positive_points.get("superficie_m2", 0)
        score += points
        reasons.append(f"superficie en m2: +{points}")

    if opportunity.get("detected_company_or_operator") or has_private_operator_signal(
        text, keywords_config
    ):
        points = positive_points.get("empresa_privada_identificada", 0)
        score += points
        reasons.append(f"empresa privada identificada: +{points}")

    if opportunity.get("sector") in keywords_config.get("priority_sectors", []):
        points = positive_points.get("sector_prioritario", 0)
        score += points
        reasons.append(f"sector prioritario: +{points}")

    return score, reasons


def score_negative_signals(text, scoring_config, keywords_config):
    score = 0
    reasons = []
    negative_points = scoring_config.get("negative_points", {})

    for rule in keywords_config.get("negative_signal_keywords", []):
        label = rule.get("label", "")
        point_key = rule.get("score_key", label)
        for keyword in rule.get("keywords", []):
            if keyword.lower() in text:
                points = negative_points.get(point_key, 0)
                score += points
                reasons.append(f"{label}: {points}")
                break

    if is_financial_only(text, keywords_config):
        points = negative_points.get("solo_resultados_financieros", 0)
        score += points
        reasons.append(f"solo resultados financieros: {points}")

    if not has_physical_space_signal(text, keywords_config):
        points = negative_points.get("sin_espacio_fisico_asociado", 0)
        score += points
        reasons.append(f"sin espacio físico asociado: {points}")

    return score, reasons


def classify_priority(score, scoring_config):
    thresholds = scoring_config.get("priority_thresholds", {})
    if score >= thresholds.get("alta", 75):
        return "Alta"
    if score >= thresholds.get("media", 50):
        return "Media"
    if score >= thresholds.get("baja", 25):
        return "Baja"
    return "Descartada"


def suggested_action(priority):
    actions = {
        "Alta": "Revisar noticia y localizar responsable del proyecto o expansión.",
        "Media": "Validar si existe proyecto físico, ubicación y calendario.",
        "Baja": "Guardar en seguimiento y revisar si aparecen nuevas señales.",
        "Descartada": "No actuar salvo que surja información más concreta.",
    }
    return actions.get(priority, "Revisar manualmente.")


def has_expected_date(text):
    date_words = [
        "en 2026",
        "en 2027",
        "este año",
        "próximo año",
        "primer trimestre",
        "segundo trimestre",
        "tercer trimestre",
        "cuarto trimestre",
        "antes de verano",
        "después de verano",
    ]
    return any(word in text for word in date_words)


def has_investment(text):
    money_words = ["millones", "millón", "inversión", "invertirá", "invertido", "euros"]
    return any(word in text for word in money_words)


def has_surface(text):
    surface_words = ["m2", "m²", "metros cuadrados", "superficie"]
    return any(word in text for word in surface_words)


def has_private_operator_signal(text, keywords_config):
    return any(
        keyword.lower() in text
        for keyword in keywords_config.get("private_operator_keywords", [])
    )


def has_physical_space_signal(text, keywords_config):
    return any(
        keyword.lower() in text
        for keyword in keywords_config.get("physical_space_keywords", [])
    )


def is_financial_only(text, keywords_config):
    has_financial = any(
        keyword.lower() in text
        for keyword in keywords_config.get("financial_only_keywords", [])
    )
    return has_financial and not has_physical_space_signal(text, keywords_config)
