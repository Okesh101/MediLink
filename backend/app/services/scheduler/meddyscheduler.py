# app/services/meddyscheduler.py

from datetime import timedelta
from app import db, scheduler
from app.models.SystemModels import TimelineEvent
from app.utils.time import lagos_now


def trigger_followup_notification(patient_public_id: str, hospital_name: str):
    """
    Executed by APScheduler after discharge timeout (mocked for 2 minutes).
    """
    with scheduler.app.app_context():
        # 1. Log Follow-up event on Patient Timeline
        timeline_entry = TimelineEvent(
            patient_public_id=patient_public_id,
            title="Automated Follow-up Check-in",
            description=f"Meddy check-in triggered following discharge from {hospital_name}.",
            event_type="FOLLOW_UP"
        )
        db.session.add(timeline_entry)
        db.session.commit()

        # 2. Trigger Mock Notification output
        print(f"\n========================================================")
        print(f"NOTIFICATION [PATIENT: {patient_public_id}]")
        print(f"Message: Hello! Meddy checking in from {hospital_name}.")
        print(f"How are you feeling 2 minutes post-discharge?")
        print(f"========================================================\n")


def schedule_patient_discharge(patient_public_id: str, hospital_name: str, delay_minutes: int = 1):
    """
    Enqueues the follow-up background job.
    """
    run_time = lagos_now() + timedelta(minutes=delay_minutes)
    job_id = f"discharge_followup_{patient_public_id}_{int(run_time.timestamp())}"

    scheduler.add_job(
        id=job_id,
        func=trigger_followup_notification,
        trigger='date',
        run_date=run_time,
        args=[patient_public_id, hospital_name]
    )
