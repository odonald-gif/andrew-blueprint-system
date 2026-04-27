import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Andrew's Motion Engine (Calendar) and Email Nexus (Gmail)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def main():
    """
    Generates the token.json file using the credentials.json.
    This will open a browser window for you to authenticate.
    """
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing existing token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"Error: Could not find '{creds_path}'.")
                print("Make sure credentials.json is inside the backend/ folder.")
                return

            print("Starting the Google Auth Flow. A browser window will pop up.")
            print("Please click 'Allow' to grant Andrew access to your Calendar and Gmail.")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    print("\n[SUCCESS] 'token.json' has been generated in the backend/ folder!")
    print("Andrew now has memory access to Google Calendar and Gmail.")

if __name__ == '__main__':
    main()
