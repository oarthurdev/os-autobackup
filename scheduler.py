from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
from database import Database
from backup_engine import BackupEngine
from logger import Logger

class BackupScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = Database()
        self.logger = logging.getLogger('BackupScheduler')
        self.scheduler.start()
        self.load_schedules()
    
    def load_schedules(self):
        active_schedules = self.db.get_active_schedules()
        
        for schedule in active_schedules:
            self.add_job(schedule)
        
        self.logger.info(f"Loaded {len(active_schedules)} active schedules")
    
    def add_job(self, schedule):
        job_id = f"schedule_{schedule['id']}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        trigger = self.create_trigger(schedule['schedule_type'], schedule['schedule_value'])
        
        if trigger:
            self.scheduler.add_job(
                func=self.execute_backup,
                trigger=trigger,
                id=job_id,
                args=[schedule['ssh_host_id'], schedule['id']],
                replace_existing=True
            )
            
            next_run = self.scheduler.get_job(job_id).next_run_time
            self.db.update_schedule(schedule['id'], next_run=next_run.isoformat() if next_run else None)
            
            self.logger.info(f"Added job {job_id} with trigger {schedule['schedule_type']}")
    
    def create_trigger(self, schedule_type, schedule_value):
        if schedule_type == 'daily':
            hour, minute = schedule_value.split(':')
            return CronTrigger(hour=int(hour), minute=int(minute))
        
        elif schedule_type == 'weekly':
            day_of_week, time = schedule_value.split(' ')
            hour, minute = time.split(':')
            return CronTrigger(day_of_week=day_of_week, hour=int(hour), minute=int(minute))
        
        elif schedule_type == 'interval_hours':
            return IntervalTrigger(hours=int(schedule_value))
        
        elif schedule_type == 'interval_days':
            return IntervalTrigger(days=int(schedule_value))
        
        elif schedule_type == 'cron':
            parts = schedule_value.split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
        
        return None
    
    def execute_backup(self, ssh_host_id, schedule_id):
        self.logger.info(f"Executing scheduled backup for host {ssh_host_id} (schedule {schedule_id})")
        
        try:
            now = datetime.now().isoformat()
            self.db.update_schedule(schedule_id, last_run=now)
            
            backup_engine = BackupEngine()
            backup_engine.perform_backup(host_id=ssh_host_id)
            
            job_id = f"schedule_{schedule_id}"
            next_run = self.scheduler.get_job(job_id).next_run_time
            self.db.update_schedule(schedule_id, next_run=next_run.isoformat() if next_run else None)
            
            self.logger.info(f"Scheduled backup completed successfully for host {ssh_host_id}")
            
        except Exception as e:
            self.logger.error(f"Error executing scheduled backup: {str(e)}")
    
    def reload_schedule(self, schedule_id):
        schedule = self.db.get_schedule(schedule_id)
        
        if schedule:
            if schedule['is_active']:
                self.add_job(schedule)
            else:
                job_id = f"schedule_{schedule_id}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    self.logger.info(f"Removed inactive job {job_id}")
    
    def remove_schedule(self, schedule_id):
        job_id = f"schedule_{schedule_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job {job_id}")
    
    def get_scheduler_status(self):
        jobs = self.scheduler.get_jobs()
        
        return {
            'running': self.scheduler.running,
            'jobs_count': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in jobs
            ]
        }
    
    def shutdown(self):
        self.scheduler.shutdown()
        self.logger.info("Scheduler shut down")

scheduler_instance = None

def get_scheduler():
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = BackupScheduler()
    return scheduler_instance
