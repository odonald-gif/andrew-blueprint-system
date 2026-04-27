import os
import logging
from typing import List, Dict, Any
import datetime

# Placeholder for actual google api imports when credentials.json is provided
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',  # Write access for time-blocking
]

class CalendarSync:
    """
    Connects to Google Calendar to read real events, passing them to the Motion logic.
    Requires a credentials.json file in the root to function fully.
    """
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Attempts to load credentials from token.json or file"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            elif os.path.exists('credentials.json'):
                logger.info("Starting Google OAuth Flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            else:
                raise RuntimeError("Calendar Sync offline: credentials.json missing. Cannot schedule deep work.")

        logger.info("Calendar authenticated successfully.")
        self.service = build('calendar', 'v3', credentials=self.creds)

    def fetch_todays_events(self) -> List[Dict[str, Any]]:
        """Fetches events for the current day to act as busy slots"""
        if self.service:
            # actual API call logic
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            end_of_day = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'
            
            logger.info('Getting today\'s upcoming events')
            try:
                events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                                      timeMax=end_of_day, singleEvents=True,
                                                      orderBy='startTime').execute()
                events = events_result.get('items', [])
                
                if not events:
                    logger.info('No upcoming events found today.')
                    return []
                    
                busy_slots = []
                for event in events:
                    start_str = event['start'].get('dateTime', event['start'].get('date'))
                    end_str = event['end'].get('dateTime', event['end'].get('date'))
                    # Convert to minutes from midnight (approx logic)
                    st = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    et = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    
                    busy_slots.append({
                        "start": st.hour * 60 + st.minute,
                        "end": et.hour * 60 + et.minute,
                        "summary": event.get('summary', 'Busy')
                    })
                return busy_slots
            except Exception as e:
                logger.error(f"Error fetching calendar: {e}")
            
        # No credentials — return empty. Never inject fake events into the scheduler.
        logger.warning("CalendarSync is unauthenticated. Returning empty schedule. Run google_auth_setup.py to fix.")
        return []

    def create_time_block(self, summary: str, start_minutes: int, duration_minutes: int, date: datetime.date = None) -> Dict[str, Any]:
        """
        Creates a calendar event to block time for deep work or tasks.
        start_minutes: minutes from midnight (e.g. 540 = 9:00 AM)
        """
        if not self.service:
            logger.warning("Cannot create time block — CalendarSync not authenticated.")
            return {"status": "error", "reason": "not_authenticated"}

        target_date = date or datetime.date.today()
        start_dt = datetime.datetime.combine(
            target_date,
            datetime.time(start_minutes // 60, start_minutes % 60)
        )
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        event_body = {
            'summary': f'[Andrew] {summary}',
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Africa/Lagos'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Africa/Lagos'},
            'description': 'Auto-blocked by Andrew Executive Assistant.',
            'colorId': '9',  # Blueberry — visually distinct
        }

        try:
            created = self.service.events().insert(calendarId='primary', body=event_body).execute()
            logger.info(f"Time block created: {created.get('htmlLink')}")
            return {"status": "success", "event_id": created['id'], "link": created.get('htmlLink')}
        except Exception as e:
            logger.error(f"Error creating time block: {e}")
            return {"status": "error", "reason": str(e)}
