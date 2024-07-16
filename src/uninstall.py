#windows libraries
import sys
import subprocess

if sys.platform in ["Linux", "darwin"]:
    pass
elif sys.platform == "win32":
    task_name = "GradescopeCalendar"
    action = "schtasks /Delete /TN "+ task_name +" /F"
    subprocess.run(action, shell=False)
    #delete the log on command too
		
