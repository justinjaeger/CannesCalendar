from datetime import datetime
import os
import re
from bs4 import BeautifulSoup

def sanitize_filename(text):
    # Remove special characters and replace spaces with underscores
    text = re.sub(r'[^\w\s-]', '', text)
    text = text.replace(' ', '_').lower()
    return text

def parse_html_file(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    screenings = []
    
    # Find all screening entries
    entries = soup.find_all('div', class_='screening-entry')
    
    for entry in entries:
        title = entry.find('h3').text.strip()
        director = entry.find('div', class_='director').text.strip()
        program = entry.find('div', class_='program').text.strip()
        theater = entry.find('div', class_='theater').text.strip()
        time = entry.find('div', class_='time').text.strip()
        
        # Parse time
        start_time, end_time = time.split(' - ')
        
        screenings.append({
            'title': title,
            'director': director,
            'program': program,
            'theater': theater,
            'start_time': start_time,
            'end_time': end_time
        })
    
    return screenings

def create_calendar_file(screenings, date_str):
    # Start the calendar file
    calendar_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Cannes Film Festival//Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Cannes Film Festival
X-WR-TIMEZONE:Europe/Paris
BEGIN:VTIMEZONE
TZID:Europe/Paris
X-LIC-LOCATION:Europe/Paris
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
"""
    
    # Add each screening as an event
    for screening in screenings:
        # Convert times to datetime objects
        start_dt = datetime.strptime(f"{date_str} {screening['start_time']}", "%Y%m%d %I:%M %p")
        end_dt = datetime.strptime(f"{date_str} {screening['end_time']}", "%Y%m%d %I:%M %p")
        
        # Format times for ics file with timezone
        start_str = start_dt.strftime("%Y%m%dT%H%M00")
        end_str = end_dt.strftime("%Y%m%dT%H%M00")
        
        # Add event to calendar
        calendar_content += f"""BEGIN:VEVENT
DTSTART;TZID=Europe/Paris:{start_str}
DTEND;TZID=Europe/Paris:{end_str}
SUMMARY:{screening['title']}
DESCRIPTION:Director: {screening['director']}<br>Program: {screening['program']}
LOCATION:{screening['theater']}
UID:{screening['title']}_{start_str}@cannesfilmfestival.com
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
END:VEVENT
"""
    
    # End the calendar file
    calendar_content += "END:VCALENDAR"
    
    # Create ics_files directory if it doesn't exist
    if not os.path.exists("ics_files"):
        os.makedirs("ics_files")
    
    # Write to file
    filename = f"may_{date_str[6:8]}.ics"
    with open(f"ics_files/{filename}", "w") as f:
        f.write(calendar_content)
    
    return filename

def process_all_days():
    # Process each day from May 14 to May 24
    for day in range(14, 25):
        html_file = f"may_{day}.html"
        if os.path.exists(html_file):
            print(f"Processing {html_file}...")
            screenings = parse_html_file(html_file)
            date_str = f"202505{day:02d}"
            ics_file = create_calendar_file(screenings, date_str)
            print(f"Created {ics_file}")

if __name__ == "__main__":
    # Remove any existing ics files
    if os.path.exists("ics_files"):
        for file in os.listdir("ics_files"):
            if file.endswith(".ics"):
                os.remove(os.path.join("ics_files", file))
    
    # Process all days
    process_all_days()
    print("All calendar files have been created successfully!") 