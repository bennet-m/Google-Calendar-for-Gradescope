from tkinter import messagebox
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from seleniumscraping import scraping
from secrets import config
import os.path
import sys
import subprocess
from macPath import *

#logger
import logging
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]



def main():
	"""Shows basic usage of the Google Calendar API.
	Prints the start and name of the next 10 events on the user's calendar.
	"""
	#windows folder path
	Win_folder_path = get_WinPath() / "GradeSync"  # Replace with your desired folder path

	#temporary need to make an installer
	if not os.path.exists(Win_folder_path):
		os.makedirs(Win_folder_path)
		logger.info(f"Folder created at {Win_folder_path}")
	else:
		print(f"Folder already exists at {Win_folder_path}")
 
 
	print("setting up Logger")
	if sys.platform in ["Linux", "darwin"]:
		logger_path = get_path() / "GradeSync.log"
	else:
		logger_path = Win_folder_path / "GradeSync.log"
	
 	#Setup Global Logger
	logging.basicConfig(filename=logger_path, encoding='utf-8', level=logging.INFO)
 
	creds = None
	#Define the token path for the google calendar api
	if sys.platform in ["Linux", "darwin"]:
		token_path = get_path() / "token.json"
	else:
		token_path = Win_folder_path / "token.json"

	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists(token_path):
		creds = Credentials.from_authorized_user_file(token_path, SCOPES)
	# If there are no (valid) token available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			logger.info("Refreshing token")
			creds.refresh(Request())
		else:
			client_config = config
			flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open(token_path, "w") as token:
			token.write(creds.to_json())

	try:
		service = build("calendar", "v3", credentials=creds)
		logger.info("running")
		# Check if the Gradescope calendar exists, if not create it
		page_token = None
		grade_scope_cal_exists = False
		while True:
			calendar_list = service.calendarList().list(pageToken=page_token).execute()
			for calendar_list_entry in calendar_list['items']:
				if calendar_list_entry['summary'] == 'Gradescope Assignments':
					grade_scope_cal_exists = True
					id = calendar_list_entry['id']
					break
			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break

		if not grade_scope_cal_exists:
			calendar = {
				'summary': 'Gradescope Assignments',
			}
			created_calendar = service.calendars().insert(body=calendar).execute()
			id = created_calendar['id']

		# Retrieve list of events
		events_result = service.events().list(calendarId=id).execute()
		events = events_result.get('items', [])

		# Delete each event
		for event in events:
			service.events().delete(calendarId=id, eventId=event['id']).execute()
			logger.info(f"Event {event['summary']} deleted.")

		# Call scraping function to get events and insert them into the calendar
		events = scraping()
		for event in events:
			if event:
				event = service.events().insert(calendarId=id, body=event).execute()
				logger.info('Event created: %s' % (event.get('htmlLink')))
    # logger.info("Not actually making events")
	except HttpError as error:
		logger.info(f"An error occurred: {error}")

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
	task_name = "GradescopeCalendar"
	executable_path = sys.argv[0]
	logger.info(executable_path)
	#run every hour
	action1 = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc minute /mo 1 /f /RL highest'
	#run on start up
	startUp_task_name = task_name + "Start"
	action2 = f'schtasks /create /tn "{startUp_task_name}" /tr "{executable_path}" /sc onstart /f /RL highest'
	subprocess.run(action1, shell=False)
	subprocess.run(action2, shell=False)

if __name__ == "__main__":
	if sys.platform in ["Linux", "darwin"]:
		setup_cronjob()
	elif sys.platform == "win32":
		setup_task_scheduler()
	try:
		main()
	except Exception as e:
            logger.info("Failed!", e)
            print("Failed!", e)
