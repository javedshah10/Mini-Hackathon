import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from db import get_supabase, update_submission_status
from pipeline import run_submission_pipeline


POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "30"))


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def poll_and_process_pending() -> None:
    client = get_supabase()
    pending = client.table("submissions").select("*").eq("status", "pending").execute().data
    threshold = datetime.now(timezone.utc) - timedelta(seconds=POLLING_INTERVAL_SECONDS)
    eligible = [s for s in pending if _parse_ts(s["created_at"]) < threshold]
    print(f"[poller] checked={len(pending)} eligible={len(eligible)} at={datetime.now(timezone.utc).isoformat()}")

    for sub in eligible:
        submission_id = sub["id"]
        update_submission_status(submission_id, "processing")
        try:
            run_submission_pipeline(submission_id)
        except Exception as exc:
            print(f"[poller] failed submission={submission_id} error={exc}")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(poll_and_process_pending, "interval", seconds=POLLING_INTERVAL_SECONDS)
    scheduler.start()
    print(f"[poller] started interval={POLLING_INTERVAL_SECONDS}s")
    return scheduler
