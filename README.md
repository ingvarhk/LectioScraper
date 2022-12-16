This extension of **Lectio Scraper**, embeds Lectio events into Google Calendar using [this api](https://developers.google.com/calendar/api).

## Preparation
Start by [creating a new project](https://console.cloud.google.com/projectcreate) at Google Cloud console. Enable the Calendar API, go to credentials, and create an OAuth 2.0 client (then download the new credentials.json file into the *src* folder). 



## Usage Example

```python
from calendar import lectioToCalendar

ltc = lectioToCalendar(lectioUsername, lectioPassword, schoolId, calendarId)
schedule1 = ltc.getFormattedSchedule("512022") # Format: WWYYYY

ltc.updateCalendar(schedule1)
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
