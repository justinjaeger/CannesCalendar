from google.oauth2 import service_account
from googleapiclient.discovery import build
import icalendar
from datetime import datetime
import pytz
import time
import re
import os

def get_calendar_service():
    """Gets an authorized Google Calendar API service instance."""
    credentials = service_account.Credentials.from_service_account_file(
        'oscar-expert-app-3b21acf1fecd.json',
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=credentials)

def delete_all_events(calendar_id):
    """Deletes all events from the specified calendar."""
    service = get_calendar_service()
    
    # Get all events
    print("Fetching events...")
    events_result = service.events().list(
        calendarId=calendar_id,
        singleEvents=True,
        orderBy='startTime',
        maxResults=2500  # Get up to 2500 events
    ).execute()
    events = events_result.get('items', [])
    
    if not events:
        print('No events found.')
        return
    
    total_events = len(events)
    print(f'Found {total_events} events. Starting deletion...')
    
    # Delete each event with retry logic
    success_count = 0
    failure_count = 0
    
    for i, event in enumerate(events, 1):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                service.events().delete(
                    calendarId=calendar_id,
                    eventId=event['id']
                ).execute()
                success_count += 1
                print(f'[{i}/{total_events}] Deleted event: {event.get("summary", "Untitled")}')
                # Add a delay between deletions to avoid rate limits
                time.sleep(0.1)
                break
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    failure_count += 1
                    print(f'[{i}/{total_events}] Failed to delete event {event.get("summary", "Untitled")}: {str(e)}')
                else:
                    print(f'Retry {retry_count}/{max_retries} for event {event.get("summary", "Untitled")}')
                    time.sleep(2)
    
    print(f'\nDeletion complete:')
    print(f'Successfully deleted: {success_count} events')
    print(f'Failed to delete: {failure_count} events')
    return success_count, failure_count

def clean_ics_content(content):
    """Clean the ICS content to ensure proper formatting."""
    # Remove any BOM characters
    content = content.decode('utf-8').replace('\ufeff', '')
    # Ensure proper line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    # Remove empty lines
    content = re.sub(r'\n\s*\n', '\n', content)
    return content.encode('utf-8')

def add_events_from_ics(calendar_id, ics_file_path):
    """Adds events from an ICS file to the specified calendar."""
    service = get_calendar_service()
    
    # Read and parse the ICS file
    print(f"\nReading ICS file: {ics_file_path}")
    try:
        with open(ics_file_path, 'rb') as f:
            content = f.read()
            content = clean_ics_content(content)
            cal = icalendar.Calendar.from_ical(content)
    except Exception as e:
        print(f"Error reading ICS file: {str(e)}")
        return 0, 0
    
    # Get all events from the calendar
    events = [component for component in cal.walk() if component.name == "VEVENT"]
    total_events = len(events)
    print(f"Found {total_events} events in ICS file. Starting to add...")
    
    # Add each event with retry logic
    success_count = 0
    failure_count = 0
    
    for i, event in enumerate(events, 1):
        max_retries = 3
        retry_count = 0
        
        try:
            # Convert event to Google Calendar format
            google_event = {
                'summary': str(event.get('summary', 'Untitled')),
                'description': str(event.get('description', '')),
                'location': str(event.get('location', '')),
                'start': {
                    'dateTime': event.get('dtstart').dt.isoformat(),
                    'timeZone': 'Europe/Paris',  # Cannes timezone
                },
                'end': {
                    'dateTime': event.get('dtend').dt.isoformat(),
                    'timeZone': 'Europe/Paris',  # Cannes timezone
                }
            }
            
            while retry_count < max_retries:
                try:
                    service.events().insert(
                        calendarId=calendar_id,
                        body=google_event
                    ).execute()
                    success_count += 1
                    print(f'[{i}/{total_events}] Added event: {google_event["summary"]}')
                    # Add a delay between additions to avoid rate limits
                    time.sleep(0.1)
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        failure_count += 1
                        print(f'[{i}/{total_events}] Failed to add event {google_event["summary"]}: {str(e)}')
                    else:
                        print(f'Retry {retry_count}/{max_retries} for event {google_event["summary"]}')
                        time.sleep(2)
        except Exception as e:
            failure_count += 1
            print(f'[{i}/{total_events}] Error processing event: {str(e)}')
    
    print(f'\nAddition complete:')
    print(f'Successfully added: {success_count} events')
    print(f'Failed to add: {failure_count} events')
    return success_count, failure_count

def replace_calendar_events(calendar_id, ics_file_path):
    """Deletes all events from a calendar and replaces them with events from an ICS file."""
    print(f"Starting calendar replacement process...")
    print(f"Calendar ID: {calendar_id}")
    print(f"ICS File: {ics_file_path}")
    print("-" * 50)
    
    # First delete all existing events
    deleted_success, deleted_failed = delete_all_events(calendar_id)
    
    # Then add new events from ICS file
    added_success, added_failed = add_events_from_ics(calendar_id, ics_file_path)
    
    print("\nFinal Summary:")
    print("-" * 50)
    print(f"Deleted: {deleted_success} events (Failed: {deleted_failed})")
    print(f"Added: {added_success} events (Failed: {added_failed})")
    print("-" * 50) 