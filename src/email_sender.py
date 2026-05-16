import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_daily_email(email_config, report_path, summary_stats):
    config = (email_config or {}).get("email", {})
    if not config.get("enabled", False):
        return {"sent": False, "reason": "envío de email desactivado"}

    smtp_host = config.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(config.get("smtp_port", 587))
    smtp_user_env = config.get("smtp_user_env", "SMTP_USER")
    smtp_password_env = config.get("smtp_password_env", "SMTP_PASSWORD")
    smtp_user = os.environ.get(smtp_user_env) or config.get("from_address", "")
    smtp_password = os.environ.get(smtp_password_env, "")

    if not smtp_user or not smtp_password:
        return {
            "sent": False,
            "reason": (
                f"faltan variables de entorno {smtp_user_env} o {smtp_password_env}"
            ),
        }

    recipients = config.get("to", [])
    if isinstance(recipients, str):
        recipients = [recipients]
    recipients = [recipient for recipient in recipients if recipient]
    if not recipients:
        return {"sent": False, "reason": "no hay destinatarios configurados"}

    report_path = Path(report_path)
    message = EmailMessage()
    message["Subject"] = config.get("subject", "Informe diario de oportunidades")
    message["From"] = config.get("from_address") or smtp_user
    message["To"] = ", ".join(recipients)
    message.set_content(build_email_body(report_path, summary_stats, config))

    if config.get("attach_html", True) and report_path.exists():
        message.add_attachment(
            report_path.read_bytes(),
            maintype="text",
            subtype="html",
            filename=report_path.name,
        )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        return {"sent": False, "reason": f"error SMTP: {exc}"}

    return {"sent": True, "reason": "email enviado correctamente"}


def build_email_body(report_path, summary_stats, config):
    lines = [
        "Informe diario generado.",
        "",
        "Resumen:",
        f"- Noticias encontradas: {summary_stats.get('Noticias encontradas', 0)}",
        (
            "- Noticias dentro del rango temporal: "
            f"{summary_stats.get('Noticias dentro del rango temporal', 0)}"
        ),
        f"- Oportunidades altas: {summary_stats.get('Oportunidades altas', 0)}",
        f"- Oportunidades medias: {summary_stats.get('Oportunidades medias', 0)}",
        f"- Oportunidades bajas: {summary_stats.get('Oportunidades bajas', 0)}",
        (
            "- Descartadas por antigüedad: "
            f"{summary_stats.get('Descartadas por antigüedad', 0)}"
        ),
        (
            "- Descartadas por otros motivos: "
            f"{summary_stats.get('Descartadas por otros motivos', 0)}"
        ),
        (
            "- Penalizadas por ya inauguradas: "
            f"{summary_stats.get('Penalizadas por ya inauguradas', 0)}"
        ),
    ]

    if config.get("include_local_report_path", True):
        lines.extend(["", f"Informe local: {report_path}"])

    if config.get("attach_html", True):
        lines.extend(["", "El informe HTML va adjunto a este correo."])

    return "\n".join(lines)
