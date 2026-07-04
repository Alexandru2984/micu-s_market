from favorites.alerts import run_saved_search_alerts
from notifications.email import send_pending_notification_emails


def send_pending_notification_emails_job(payload):
    limit = int(payload.get("limit", 100))
    return {"sent": send_pending_notification_emails(limit=limit)}


def saved_search_alerts_job(payload):
    limit_per_search = int(payload.get("limit_per_search", 20))
    return run_saved_search_alerts(limit_per_search=limit_per_search)


JOB_HANDLERS = {
    "notifications.send_pending_emails": send_pending_notification_emails_job,
    "favorites.saved_search_alerts": saved_search_alerts_job,
}


def get_job_handler(name):
    try:
        return JOB_HANDLERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown background job: {name}") from exc
