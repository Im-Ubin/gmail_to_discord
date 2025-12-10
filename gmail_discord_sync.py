#!/usr/bin/env python3
"""
Gmail to Discord Sync Bot
Monitors Gmail inbox and sends new emails to Discord channels based on keywords
"""

import os
import json
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Color mapping for Discord embeds
COLORS = {
    'red': 0xFF0000,
    'green': 0x00FF00,
    'blue': 0x0099FF,
    'yellow': 0xFFFF00,
    'purple': 0x9B59B6,
    'orange': 0xFF9900,
    'pink': 0xFF69B4,
    'teal': 0x1ABC9C,
    'default': 0x7289DA
}


def load_config() -> Dict:
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Please create it from config.example.json")
        raise
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config.json: {e}")
        raise


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    
    # Load credentials from environment variable (for GitHub Actions)
    if os.getenv('GMAIL_CREDENTIALS'):
        creds_data = json.loads(os.getenv('GMAIL_CREDENTIALS'))
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    # Load from token.json (for local testing)
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If credentials are invalid or don't exist, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("credentials.json not found. Please download it from Google Cloud Console")
                raise FileNotFoundError("credentials.json")
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("Gmail authentication successful")
        print("Copy the contents of token.json to GitHub Secrets as GMAIL_CREDENTIALS")
    
    return build('gmail', 'v1', credentials=creds)


def get_last_check_time() -> datetime:
    """Get the last check time from file, or default to 24 hour ago"""
    try:
        if os.path.exists('last_check.txt'):
            with open('last_check.txt', 'r') as f:
                timestamp = f.read().strip()
                return datetime.fromisoformat(timestamp)
    except Exception as e:
        print(f"Could not read last check time: {e}")
    
    # Default to 24 hour ago
    return datetime.now() - timedelta(hours=24)


def save_last_check_time():
    """Save current time as last check time"""
    with open('last_check.txt', 'w') as f:
        f.write(datetime.now().isoformat())


def get_new_emails(service, after_date: datetime) -> List[Dict]:
    """Fetch new emails after the specified date"""
    try:
        # Convert datetime to Gmail query format
        query = f'after:{int(after_date.timestamp())}'
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50  # Adjust as needed
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No new emails found")
            return []
        
        print(f"Found {len(messages)} new email(s)")
        
        # Fetch full message details
        emails = []
        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                emails.append(parse_email(message))
            except HttpError as e:
                print(f"Error fetching email {msg['id']}: {e}")
                continue
        
        return emails
    
    except HttpError as e:
        print(f"Gmail API error: {e}")
        return []


def parse_email(message: Dict) -> Dict:
    """Parse Gmail message into simplified format"""
    headers = {h['name']: h['value'] for h in message['payload']['headers']}
    
    # Get email body
    body = ''
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
    elif 'body' in message['payload'] and 'data' in message['payload']['body']:
        body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
    
    # Truncate body if too long
    if len(body) > 500:
        body = body[:500] + '...'
    
    return {
        'id': message['id'],
        'subject': headers.get('Subject', '(No Subject)'),
        'from': headers.get('From', 'Unknown'),
        'date': headers.get('Date', ''),
        'body': body,
        'snippet': message.get('snippet', '')
    }


def extract_email_address(from_field: str) -> str:
    """Extract email address from 'From' field (e.g., 'Name <email@example.com>' -> 'email@example.com')"""
    match = re.search(r'<(.+?)>', from_field)
    if match:
        return match.group(1)
    return from_field


def match_keywords(email: Dict, keyword_config: Dict) -> bool:
    """Check if email matches any keywords in the configuration"""
    subject = email['subject'].lower()
    from_email = extract_email_address(email['from']).lower()
    
    # Check each keyword
    for keyword in keyword_config['keywords']:
        keyword_lower = keyword.lower()
        if keyword_lower in subject or keyword_lower in from_email:
            return True
    
    return False


def get_color_value(color_name: str) -> int:
    """Convert color name or hex to Discord color integer"""
    if isinstance(color_name, int):
        return color_name
    
    # Check if it's a hex color
    if color_name.startswith('#'):
        return int(color_name[1:], 16)
    
    # Look up color name
    return COLORS.get(color_name.lower(), COLORS['default'])


def send_to_discord(email: Dict, webhook_url: str, color: str = 'default'):
    """Send email to Discord channel via webhook"""
    
    # Create embed
    embed = {
        'title': f'📧 {email["subject"]}',
        'color': get_color_value(color),
        'fields': [
            {
                'name': '발신자',
                'value': email['from'],
                'inline': False
            },
            {
                'name': '받은 시간',
                'value': email['date'],
                'inline': False
            }
        ],
        'footer': {
            'text': 'Gmail to Discord Bot'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Add body preview if available
    if email['snippet']:
        embed['description'] = email['snippet'][:300]
    
    payload = {
        'embeds': [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"Sent to Discord: {email['subject'][:50]}")
        else:
            print(f"⚠️  Discord webhook error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Failed to send to Discord: {e}")


def process_emails(emails: List[Dict], config: Dict):
    """Process emails and send to appropriate Discord channels"""
    if not emails:
        return
    
    sent_count = 0
    
    for email in emails:
        matched = False
        
        # Check each keyword configuration
        for keyword_config in config['keywords']:
            if match_keywords(email, keyword_config):
                send_to_discord(
                    email,
                    keyword_config['webhook'],
                    keyword_config.get('color', 'default')
                )
                matched = True
                sent_count += 1
        
        # Send to default webhook if no keywords matched
        if not matched and config.get('default_webhook'):
            send_to_discord(
                email,
                config['default_webhook'],
                config.get('default_color', 'default')
            )
            sent_count += 1
    
    print(f"Processed {len(emails)} email(s), sent {sent_count} message(s) to Discord")


def main():
    """Main function"""
    print("Starting Gmail to Discord sync...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = load_config()
        
        # Authenticate with Gmail
        service = get_gmail_service()
        
        # Get last check time
        last_check = get_last_check_time()
        print(f"Checking emails since: {last_check.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch new emails
        emails = get_new_emails(service, last_check)
        
        # Process and send to Discord
        process_emails(emails, config)
        
        # Update last check time
        save_last_check_time()
        
        print("Sync completed successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
