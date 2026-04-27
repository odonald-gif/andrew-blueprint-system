import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger("YouTubeFleet")

class YouTubeFleetUploader:
    """
    Manages OAuth tokens for multiple Google accounts and uploads 
    generated videos to their respective YouTube channels.
    """
    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/yt-analytics.readonly',
        'https://www.googleapis.com/auth/youtube.readonly'
    ]

    def __init__(self, token_dir: str = "data/youtube_tokens"):
        self.token_dir = token_dir
        if not os.path.exists(self.token_dir):
            os.makedirs(self.token_dir)

    def _get_credentials(self, account_identifier: str):
        """
        Gets valid user credentials from storage.
        Requires client_secrets.json downloaded from Google Cloud Console.
        """
        creds = None
        token_path = os.path.join(self.token_dir, f"{account_identifier}_token.json")
        client_secrets_path = os.path.join(self.token_dir, "client_secrets.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(client_secrets_path):
                    logger.error(f"Missing {client_secrets_path}. Cannot authenticate new account.")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, self.SCOPES)
                # In a headless server, this needs to be a console flow or out-of-band flow
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        return creds

    def upload_video(self, account_identifier: str, file_path: str, title: str, description: str, tags: list, category_id: str = "22") -> dict:
        """
        Uploads a video to YouTube.
        category_id 22 = People & Blogs, 28 = Science & Technology.
        """
        logger.info(f"Initiating upload for account: {account_identifier}")
        creds = self._get_credentials(account_identifier)
        if not creds:
            return {"status": "error", "message": "Authentication failed or missing secrets."}

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100], # YouTube title limit
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": "private", # Upload as private first for safety
                "selfDeclaredMadeForKids": False
            }
        }

        logger.info(f"Uploading {file_path}...")
        try:
            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
            )
            
            response = insert_request.execute()
            logger.info(f"Video uploaded successfully! Video ID: {response.get('id')}")
            return {
                "status": "success",
                "video_id": response.get('id'),
                "url": f"https://youtu.be/{response.get('id')}"
            }
            
        except Exception as e:
            logger.error(f"An HTTP error occurred: {e}")
            return {"status": "error", "message": str(e)}

youtube_fleet = YouTubeFleetUploader()
