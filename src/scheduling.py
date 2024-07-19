import sys
import subprocess
import os
import logging
from uI import get_admin_permission

logger = logging.getLogger(__name__)

#Scheduler
def get_self_path():
	if getattr(sys, 'frozen', False):
		return sys.executable
	else:
		return os.path.abspath(__file__)


#Mac Scheduler
def setup_cronjob():
    executable_path = get_self_path()
    
    cron_job = f"0 * * * * {executable_path}\n"
    current_cron_jobs = os.popen('crontab -l').read()

    if cron_job not in current_cron_jobs:
        os.system(f'(crontab -l; echo "{cron_job}") | crontab -')
        logger.info("Cron job added.")
    else:
        logger.info("Cron job already exists.")


#Windows scheduler
def setup_task_scheduler():
    from elevate import elevate
    elevate(show_console = False)
    task_name = "GradescopeCalendar"
    executable_path = get_self_path
    logger.info(executable_path)
    #run every hour
    action1 = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc minute /mo 30 /f /RL highest'
    #run on start up
    startUp_task_name = task_name + "Start"
    action2 = f'schtasks /create /tn "{startUp_task_name}" /tr "{executable_path}" /sc onstart /f /RL highest'
    subprocess.run(action1, shell=False)
    subprocess.run(action2, shell=False)


def set_up_scheduler():
    if get_admin_permission():
        if sys.platform == "darwin":
            setup_cronjob()
        elif sys.platform == "win32":
            setup_task_scheduler()
        else:
            logger.info("Scheduler not supported on this platform.")
