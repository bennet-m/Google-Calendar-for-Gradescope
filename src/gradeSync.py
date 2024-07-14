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
from pathlib import Path
import platform
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
	"""Shows basic usage of the Google Calendar API.
	Prints the start and name of the next 10 events on the user's calendar.
	"""
	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if sys.platform in ["Linux", "darwin"]:
		home_dir = Path.home()
		token_path = home_dir / "token.json"
		# token_path = "../__file__"
	else:
		token_path = "token.json"

	if os.path.exists("token.json"):
		creds = Credentials.from_authorized_user_file("token.json", SCOPES)
	# If there are no (valid) token available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			print("Refreshing token")
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
		print("running")
		# Check if the Gradescope calendar exists, if not create it
		page_token = None
		gradescopeCalExists = False
		while True:
			calendar_list = service.calendarList().list(pageToken=page_token).execute()
			for calendar_list_entry in calendar_list['items']:
				if calendar_list_entry['summary'] == 'Gradescope Assignments':
					gradescopeCalExists = True
					id = calendar_list_entry['id']
					break
			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break

		if not gradescopeCalExists:
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
			print(f"Event {event['summary']} deleted.")

		# Call scraping function to get events and insert them into the calendar
		events = scraping()
		for event in events:
			if event:
				event = service.events().insert(calendarId=id, body=event).execute()
				print('Event created: %s' % (event.get('htmlLink')))
    # print("Not actually making events")
	except HttpError as error:
		print(f"An error occurred: {error}")

#Scheduler
def get_self_path():
	if getattr(sys, 'frozen', False):
		return sys.executable
	else:
		return os.path.abspath(__file__)

#Mac Scheduler
def setup_cronjob():
	executable_path = get_self_path()
	
	cron_job = f"0 */2 * * * {executable_path}\n"
	current_cron_jobs = os.popen('crontab -l').read()

	if cron_job not in current_cron_jobs:
		os.system(f'(crontab -l; echo "{cron_job}") | crontab -')
		print("Cron job added.")
	else:
		print("Cron job already exists.")

#Windows scheduler
def setup_task_scheduler():
	task_name = "GradescopeCalendar"
	executable_path = sys.argv[0]
	print(executable_path)
	#run every hour
	action1 = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc hourly /mo 1 /f'
	#run on start up
	startUp_task_name = task_name + "Start"
	action2 = f'schtasks /create /tn "{startUp_task_name}" /tr "{executable_path}" /sc onstart /f'
	subprocess.run(action1, shell=False)
	subprocess.run(action2, shell=False)

if __name__ == "__main__":
	if sys.platform in ["Linux", "darwin"]:
		setup_cronjob()
	elif sys.platform == "win32":
		setup_task_scheduler()
	main()
