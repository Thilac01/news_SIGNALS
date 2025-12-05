from apscheduler.schedulers.background import BackgroundScheduler
from app.services.data_processor import run_pipeline
import atexit
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

scheduler = None
current_interval = 15

def start_scheduler():
    global scheduler, current_interval
    if scheduler is None:
        scheduler = BackgroundScheduler()
        # Run every 15 minutes by default
        scheduler.add_job(func=run_pipeline, trigger="interval", minutes=current_interval, id='pipeline_job')
        scheduler.start()
        logger.info(f"Scheduler started. Pipeline will run every {current_interval} minutes.")
        
        # Run immediately on startup
        scheduler.add_job(func=run_pipeline, trigger="date", id='startup_job')

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())

def refresh_now():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.add_job(func=run_pipeline, trigger="date", id=f'manual_refresh_{datetime.now().timestamp()}')
        return True
    return False

def update_interval(minutes):
    global scheduler, current_interval
    if scheduler and scheduler.running:
        try:
            scheduler.reschedule_job('pipeline_job', trigger='interval', minutes=minutes)
            current_interval = minutes
            logger.info(f"Rescheduled pipeline to run every {minutes} minutes.")
            return True
        except Exception as e:
            logger.error(f"Failed to reschedule: {e}")
            return False
    return False

def get_next_run_time():
    global scheduler
    if scheduler:
        job = scheduler.get_job('pipeline_job')
        if job:
            return str(job.next_run_time)
    return "Unknown"

def get_interval():
    return current_interval
