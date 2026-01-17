import os
import base64
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """
    Authenticates the user and returns the Gmail service.
    Expects 'credentials.json' in the current directory.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Missing 'credentials.json'. Please download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_user_email(service):
    """Get the authenticated user's email address."""
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('emailAddress')

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(service, user_id, message):
    """Send an email message."""
    try:
        response = service.users().messages().send(userId=user_id, body=message).execute()
        return response
    except Exception as e:
        print(f'An error occurred: {e}')
        raise e # Re-raise to be caught by the caller
