from notifications.email import send_pending_notification_emails


def send_pending_notification_emails_job(payload):
    limit = int(payload.get("limit", 100))
    return {"sent": send_pending_notification_emails(limit=limit)}


JOB_HANDLERS = {
    "notifications.send_pending_emails": send_pending_notification_emails_job,
}


def get_job_handler(name):
    try:
        return JOB_HANDLERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown background job: {name}") from exc
