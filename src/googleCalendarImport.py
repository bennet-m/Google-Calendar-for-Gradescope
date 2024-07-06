import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from seleniumscraping import scraping

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) token available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      print("Refreshing token")
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
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

    # Call scraping function to get events and insert them into the calendar
    events = scraping()
    for event in events:
      event = service.events().insert(calendarId='primary', body=event).execute()
      print('Event created: %s' % (event.get('htmlLink')))


  except HttpError as error:
    print(f"An error occurred: {error}")
  
if __name__ == "__main__":
  main()