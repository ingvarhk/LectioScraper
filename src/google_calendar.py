import os, sys
import datetime
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from lectio import Lectio

class lectioToCalendar:
    server_dir = Path(os.path.dirname(__file__)).parents[0] / 'server'
    def __init__(self, usr, psw, schl_id, cal_id):
        self.user_name = usr
        self.password = psw
        self.school_id = schl_id
        try:
            # full_path = os.path.dirname(__file__) 
            try:
                f = open(str(self.server_dir) + '/abbreviations.json')
            except:
                print("Could not open file 'abbreviations.json'")
            self.codes = json.load(f)
        except:
            print("File 'abbreviations.json' not found.")
            
        # # Load abbreviations/codes for activities
        # if os.path.exists('abbreviations.json'):
        #     f = open('abbreviations.json')
        #     self.codes = json.load(f)
        # else:
        #     raise Exception("File 'abbreviations.json' not found :(")


        # Define id of target calendar - use 'service.calendarList()' to see all id's
        self.calendarId = cal_id

        # Define scope, Google Calendar API
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.events']

        # Load Google API OAuth2 token
        self.creds = None

        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)

        self.checkCredentials()

    def checkCredentials(self):
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token: # Refresh token if expired
                self.creds.refresh(Request())

            else: #Login if no credentials are found
                # cred_file = se
                flow = InstalledAppFlow.from_client_secrets_file(str(self.server_dir) + '/credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)

    def lessonCodeToText(self, code):
        # Finds matching names for abbreviations/codes of activities
        new_name = code

        for i in self.codes:
            if i == code:
                new_name = self.codes[i]
        return new_name

    def getFormattedSchedule(self, week):
        # Gets Lectio schedule and formats to Google Calendar format

        # Login using LectioScraper - [https://github.com/fredrikj31/LectioScraper]
        self.lec = Lectio(self.user_name, self.password, self.school_id)

        # Refreshing Google Calendar API token if expired
        self.checkCredentials()

        # Scrape schedule form Lectio
        lectio_scheme = self.lec.getSchedule(week)
        Schedule = []

        # Formatting all events in the given week
        for lectio_event in lectio_scheme:

            if lectio_event["Status"] == "Aflyst!" or "studiecafe" in str(lectio_event["Title"]).lower(): continue
            if lectio_event["Time"] == " ": continue

            if lectio_event["Title"] == " ":
                # Set title to generic if none are specified
                summary = self.lessonCodeToText(lectio_event["Team"])
            else:
                if lectio_event["Team"] != " ":
                    summary = lectio_event["Title"] + " - " + self.lessonCodeToText(lectio_event["Team"])
                else:
                    summary = lectio_event["Title"]

            if lectio_event["Status"] == "Ændret!":
                color = "2" #bold green (10)
            else:
                color = "1" #bold blue (9)

            location = None
            if lectio_event["Room"] != " ":
                location = "Lokale: " + lectio_event["Room"]

            description = ""
            if lectio_event["Teacher"] != " ":
                description = lectio_event["Teacher"]

            if lectio_event["Note"] != []:
                # Listing notes using basic html (only works in google calendar)

                note_txt = "<ul>"
                used_notes = []

                for note in lectio_event["Note"]:
                    if note[:2] == "- ":
                        # Bullet point found, adding and looking for sub-bullet points
                        if note[2:] != "" and not note[2:].isspace():
                            note_txt += "<li>" + note[2:] + "</li>"

                        search_for_quote = True
                        stop_search = False

                        for i in lectio_event["Note"]:
                            if stop_search == True:
                                break

                            if search_for_quote == True:
                                if i == note:
                                    search_for_quote = False
                            else:
                                # Continuing from parent bullet point
                                if i[:2] == "- ":
                                    # No sub-bullet points were found
                                    stop_search = True

                                else:

                                    if i.lstrip()[:1] == "(" and i[-1:] == ")":
                                        # If only one sub-point
                                        if i.lstrip()[1:][:-1] != "" and not i.lstrip()[1:][:-1].isspace():
                                            note_txt += "<ul><li>" + i.lstrip()[1:][:-1] + "</li></ul>"
                                        stop_search = True

                                    else:
                                        if i.lstrip()[:1] == "(":
                                            # First sub-point
                                            if i.lstrip()[1:] != "" and not i.lstrip()[1:].isspace():
                                                note_txt += "<ul><li>" + i.lstrip()[1:] + "</li>"

                                        elif i[-1:] == ")":
                                            # Last sub-point
                                            if i.lstrip()[:-1] != "" and not i.lstrip()[:-1].isspace():
                                                note_txt += "<li>" + i.lstrip()[:-1] + "</li></ul>"
                                            stop_search = True

                                        else:
                                            # Middle sub-point
                                            if i.lstrip() != "" and not i.lstrip().isspace():
                                                note_txt += "<li>" + i.lstrip() + "</li>"

                                    used_notes.append(i)
                    else:
                        if note not in used_notes:
                            # Edge case notes
                            if note != "" and not note.isspace():
                                note_txt += "<li>" + note.replace("•", "").lstrip() + "</li>"


                if note_txt != "<ul>":
                    if lectio_event["Teacher"] != " ":
                        # Line break to make space between lines
                        description += "<br><br>"

                    description += "<b>Lektier:</b> " + note_txt.replace("[...]", "") + "</ul>"
                else:
                    if lectio_event["Teacher"] != " " and lectio_event["Id"] != " ":
                        # Line break to make space between lines
                        description += "<br>"
            else:
                if lectio_event["Teacher"] != " " and lectio_event["Id"] != " ":
                    # Line break to make space between lines
                    description += "<br>"

            # Adding link to the original Lectio event
            if lectio_event["Id"] != " ":
                description += '<a href="https://www.lectio.dk/lectio/' + self.school_id + '/' + lectio_event["EventLink"] + lectio_event["Id"] + '">Læs mere</a>'

            # Formatting date and time to correct format - from "DD/MM-YYY HH:MM til HH:MM" to "YYYY-MM-DDTHH:MM:SS.MMMZ"
            times = lectio_event["Time"].split(" til ")
            date = times[0].split()[0].split("-")
            formatted_date = date[1] + "-" + date[0].split("/")[1] + "-" + date[0].split("/")[0]


            dateTime_start = formatted_date + 'T' + times[0].split()[1] + ':00+02:00' # normally +01:00, but had to adjust for daylight savings
            dateTime_end = formatted_date + 'T' + times[1] + ':00+02:00'

            # Building dict with all necessary information
            event = {
              'id': lectio_event["Id"],
              'summary': summary,
              'description': description,
              'locked': 'true',
              'colorId': color,
              'source.title': "Lectio event",
              'source.url': 'https://www.lectio.dk/lectio/' + self.school_id + '/aktivitet/aktivitetforside2.aspx?absid=' + lectio_event["Id"],
              'start': {
                'dateTime': dateTime_start,
                'timeZone': 'Europe/Copenhagen',
              },
              'end': {
                'dateTime': dateTime_end,
                'timeZone': 'Europe/Copenhagen',
              }
            }

            if location != None:
                # If location is relevant, then add it
                event['location'] = location

            if lectio_event["Id"] == " ":
                # If event doesn't have an ID, then make one
                event['id'] = dateTime_start.replace("T","").replace("+","").replace(":","").replace("-","") + dateTime_end.replace("T","").replace("+","").replace(":","").replace("-","")

            # Append to list of all events
            Schedule.append(event)

        return Schedule

    def updateCalendar(self, weekSchedule):
        if weekSchedule == []:
            #print("Empty week schedule: " + str(weekSchedule))
            return

        # Calculating first datetime of week
        first_event_datetime = datetime.datetime.strptime(weekSchedule[0]["start"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
        week_start_datetime = (first_event_datetime - datetime.timedelta(days=first_event_datetime.weekday())).replace(minute=0, hour=0, second=0)
        week_end_datetime = (week_start_datetime + datetime.timedelta(days=6)).replace(minute=59, hour=23, second=59)

        #print(week_start_datetime.strftime("%Y-%m-%dT%H:%M:%S+01:00"))
        #print(week_end_datetime.strftime("%Y-%m-%dT%H:%M:%S+01:00"))

        # Getting events from calendar
        events = self.service.events().list(calendarId=self.calendarId, timeMin=week_start_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00"), timeMax=week_end_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00")).execute()

        old_events = []
        new_events = []

        for old_event in events['items']:
            old_events.append(old_event["id"])

        for new_event in weekSchedule:
            new_events.append(new_event["id"])

        extra_events = []
        missing_events = []

        # Looking for differences between Google Calendar and Lectio schedule
        if sorted(new_events) != sorted(old_events):
            extra_events = list(set(sorted(old_events)) - set(sorted(new_events)))
            missing_events = list(set(sorted(new_events)) - set(sorted(old_events)))

        #print("Extra events (to be deleted): " + str(extra_events))
        #print("Missing events (to be added): " + str(missing_events))

        for extra_event in extra_events:
            # Deleting extra events
            try:
                self.service.events().delete(calendarId=self.calendarId, eventId=extra_event).execute()
            except:
                print("Unable to delete event: " + extra_event)

        for missing_event in missing_events:
            for event in weekSchedule:
                if event["id"] == missing_event:
                    # Inserting new events into specified Google Calendar
                    try:
                        self.service.events().insert(calendarId=self.calendarId, body=event).execute()
                    except HttpError:
                        # Updating missing events for specified Google Calendar
                        try:
                            self.service.events().update(calendarId=self.calendarId, eventId=missing_event, body=event).execute()
                        except:
                            print("Unable to add missing event: " + missing_event)

        # Updating remaining events for specified Google Calendar
        for i in weekSchedule:
            if i["id"] not in extra_events and i["id"] not in missing_events:
                try:
                    # Updating existing event
                    self.service.events().update(calendarId=self.calendarId, eventId=i['id'], body=i).execute()
                except:
                    print("Unable to update existing event: " + i['id'])

        #print("Weekly schedule updated!")

