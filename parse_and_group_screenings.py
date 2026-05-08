from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from pathlib import Path
import re
import uuid
from theaters import THEATERS, format_location

def _extract_idproj_from_href(href: str | None) -> str | None:
    if not href:
        return None
    # Examples seen in the wild:
    # - "https://.../fiche?idproj=ABC%3D"
    # - "/fiche?idproj=ABC%3D"
    # - "fiche?idproj=ABC%3D"
    m = re.search(r"(?:\\?|&)idproj=([^&#]+)", href, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1)

def parse_screening_time(time_str):
    try:
        # Convert time string (e.g., "8:45 am") to datetime object
        time_obj = datetime.strptime(time_str.strip().lower(), "%I:%M %p")
        return time_obj
    except ValueError:
        print(f"Warning: Invalid time format: {time_str}")
        return None

def fold_line(line):
    """Fold long lines according to iCalendar specification (RFC 5545)"""
    if len(line) <= 75:
        return line
    parts = []
    while line:
        if len(line) <= 75:
            parts.append(line)
            break
        # Try to find a good break point
        split_at = 75
        # Don't break in the middle of a URL or escaped character
        if 'href=' in line[:75]:
            # Find the end of the URL
            url_end = line.find('\\">Event link</a>', 75)
            if url_end != -1:
                split_at = url_end + 19  # Length of '\\">Event link</a>'
        else:
            # Try to break at a space
            last_space = line[:75].rfind(' ')
            if last_space > 0:
                split_at = last_space
        parts.append(line[:split_at])
        line = ' ' + line[split_at:].lstrip()  # Space at start of continuation line
    return '\r\n'.join(parts)

def escape_text(text):
    """Escape special characters in text fields according to iCalendar spec"""
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

def create_ics_content(program_screenings):
    # Create the ICS file header
    header = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Cannes Film Festival//Screenings//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Cannes Film Festival Screenings
X-WR-TIMEZONE:Europe/Paris
"""
    
    # Process each program's screenings
    program_events = defaultdict(list)
    
    for program, screenings in program_screenings.items():
        for screening in screenings:
            try:
                # Parse the start and end times
                start_time = parse_screening_time(screening['start_time'])
                end_time = parse_screening_time(screening['end_time'])
                
                # Skip if either time is invalid
                if not start_time or not end_time:
                    print(f"Skipping screening '{screening['title']}' due to invalid time format")
                    continue
                
                # Create datetime objects for the event
                event_date = screening['date']
                start_datetime = datetime.combine(event_date, start_time.time())
                end_datetime = datetime.combine(event_date, end_time.time())
                
                # If end time is before start time, it means it ends the next day
                if end_datetime < start_datetime:
                    end_datetime += timedelta(days=1)
                
                # Convert to UTC
                paris_tz = pytz.timezone('Europe/Paris')
                start_datetime = paris_tz.localize(start_datetime).astimezone(pytz.UTC)
                end_datetime = paris_tz.localize(end_datetime).astimezone(pytz.UTC)
                
                # Get theater location
                theater = screening['theater']
                if theater not in THEATERS:
                    raise ValueError(
                        f"Unknown theater '{theater}'. Add it to THEATERS in theaters.py"
                    )
                location = format_location(THEATERS[theater])
                
                # Format the event description
                description = f"Program: {screening['program']}<br>Director: {screening['director']}<br>Theater: {theater}"
                if screening.get('id_proj'):
                    ticket_link = f"https://ticketonline1.festival-cannes.com/fiche?idproj={screening['id_proj']}"
                    description += f"<br><a href=\"{ticket_link}\">Event link</a>"
                
                # Escape special characters
                description = escape_text(description)
                
                # Fold long lines according to iCalendar spec
                description = fold_line(description)
                
                # Create the event
                event = f"""BEGIN:VEVENT
UID:{str(uuid.uuid4())}
DTSTART:{start_datetime.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_datetime.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{escape_text(f"{screening['title']} - {theater}")}
LOCATION:{location}
DESCRIPTION:{description}
END:VEVENT
"""
                program_events[program].append(event)
                
            except Exception as e:
                print(
                    f"Error creating event for screening '{screening.get('title', 'Unknown')}'. "
                    f"theater='{screening.get('theater', 'Unknown')}'. error={e}"
                )
                raise
    
    return header, program_events

def parse_html_content(content, date):
    soup = BeautifulSoup(content, 'html.parser')
    screenings = []
    
    # Find all screening divs
    screening_divs = soup.find_all('div', class_='VignetteSeance')
    
    for div in screening_divs:
        try:
            # Extract screening information
            title = div.find('label', id='lbTitre').text.strip()
            
            # Find director (it's in a label with specific style)
            director_label = div.find('label', style=lambda x: x and 'color:#7e7e7e' in x and 'font-size:12px' in x and 'font-family:\'Camphor W01 Bold\'' in x)
            director = director_label.text.strip() if director_label else "Unknown"
            
            # Find program/section
            section_div = div.find('div', id='divSection')
            program = section_div.find('label', id='lbSection').text.strip() if section_div else "Unknown"
            
            # Find theater
            theater_label = div.find('label', style=lambda x: x and 'text-transform:uppercase' in x)
            theater = theater_label.text.strip() if theater_label else "Unknown"
            
            # Find and extract idproj from href
            id_proj = None
            if div.parent and div.parent.name == 'a' and 'href' in div.parent.attrs:
                id_proj = _extract_idproj_from_href(div.parent.get('href'))
            
            # Get start and end times
            time_div = div.find('div', class_='Heure')
            if time_div:
                start_time_label = time_div.find('label', style=lambda x: x and 'color:#c5a26e' in x and 'font-size:15px' in x)
                start_time = start_time_label.text.strip() if start_time_label else "Unknown"
                
                end_time_labels = time_div.find_all('label', style=lambda x: x and 'color:#7e7e7e' in x and 'font-size:12px' in x)
                end_time = None
                for label in end_time_labels:
                    if 'END' not in label.text:
                        end_time = label.text.strip()
                        break
                if not end_time:
                    end_time = "Unknown"
            else:
                start_time = "Unknown"
                end_time = "Unknown"
            
            screenings.append({
                'title': title,
                'director': director,
                'program': program,
                'theater': theater,
                'start_time': start_time,
                'end_time': end_time,
                'date': date,
                'id_proj': id_proj
            })
        except Exception as e:
            print(f"Error parsing screening: {e}")
            continue
    
    return screenings

def parse_html_file(html_file, date=None):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if date is None:
        # Back-compat: infer date from filename (e.g., may_14.html -> May 14, 2025)
        date_str = os.path.basename(html_file).replace('.html', '').split('_')
        month = date_str[0].capitalize()
        day = date_str[1]
        date = datetime.strptime(f"{month} {day} 2025", "%B %d %Y").date()

    return parse_html_content(content, date)

def write_program_calendar(header, events, program_name, output_dir):
    # Create a safe filename from the program name
    safe_filename = re.sub(r'[^\w\s-]', '', program_name).strip().replace(' ', '_')
    # Ensure Unknown program is saved as Other
    if safe_filename == "Unknown":
        safe_filename = "Other"
    output_path = Path(output_dir) / f"{safe_filename}.ics"
    
    # IMPORTANT: Write with explicit CRLF (\r\n). Do not set newline to '\r\n' here,
    # or Python may translate \n and produce \r\r\n which breaks Google Calendar import.
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        def crlf(s: str) -> str:
            return s.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')

        # Header
        header_lines = [ln.strip() for ln in header.splitlines() if ln.strip()]
        f.write(crlf('\n'.join(header_lines)))
        f.write('\r\n\r\n')  # blank line between header and events

        # Events
        for event in events:
            f.write(crlf(event).rstrip('\r\n'))
            f.write('\r\n\r\n')  # blank line between events

        # Footer
        f.write('END:VCALENDAR\r\n')

def main():
    # Create output directory if it doesn't exist
    output_dir = Path('calendar_files/programs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each HTML file
    html_files = [f for f in os.listdir('.') if f.endswith('.html') and f.startswith('may_')]
    
    # Sort the files by date
    html_files.sort(key=lambda x: int(x.split('_')[1].replace('.html', '')))
    
    # Group all screenings by program
    program_screenings = defaultdict(list)
    
    # Process each file
    for html_file in html_files:
        print(f"Processing {html_file}...")
        screenings = parse_html_file(html_file)
        
        # Group screenings by program
        for screening in screenings:
            program = screening['program']
            # Group all Cannes Classics events together
            if program.startswith('Cannes Classics'):
                program = 'Cannes Classics'
            # Group all Cinéma de la Plage events together
            if program.startswith('Cinéma de la Plage'):
                program = 'Cinéma de la Plage'
            program_screenings[program].append(screening)
    
    # Create ICS content for each program
    header, program_events = create_ics_content(program_screenings)
    
    # Write separate files for each program
    for program, events in program_events.items():
        write_program_calendar(header, events, program, output_dir)
        print(f"Created calendar for: {program}")

if __name__ == '__main__':
    main() 