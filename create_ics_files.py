from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import os
import re
from typing import Dict, Iterable, Tuple

import requests

from parse_and_group_screenings import create_ics_content, parse_html_content, write_program_calendar
from schedule_sources import DATE_TO_URL

BASE_DIR = Path(__file__).resolve().parent

def sanitize_filename(text):
    # Remove special characters and replace spaces with underscores
    text = re.sub(r'[^\w\s-]', '', text)
    text = text.replace(' ', '_').lower()
    return text

def _parse_iso_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()

def fetch_html(url: str, timeout_s: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) CannesCalendarBot/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout_s, allow_redirects=True)
    resp.raise_for_status()
    return resp.text

def _write_debug_html(iso_day: str, html: str) -> Path:
    debug_dir = BASE_DIR / "debug_html"
    debug_dir.mkdir(parents=True, exist_ok=True)
    out = debug_dir / f"{iso_day}.html"
    out.write_text(html, encoding="utf-8")
    return out

def iter_html_inputs(html_dir: Path) -> Iterable[Tuple[str, Path]]:
    """
    Yield (iso_day, path) for files named like YYYY-MM-DD.html.
    """
    for path in sorted(html_dir.glob("*.html")):
        iso_day = path.stem
        # Validate filename format early so we fail loudly if something is off.
        _parse_iso_date(iso_day)
        yield iso_day, path

def generate_program_ics_from_html_dir(html_dir: Path) -> None:
    if not html_dir.exists():
        raise SystemExit(f"Missing html directory: {html_dir}")

    inputs = list(iter_html_inputs(html_dir))
    if not inputs:
        raise SystemExit(f"No HTML files found in: {html_dir} (expected YYYY-MM-DD.html)")

    output_dir = BASE_DIR / "calendar_files" / "programs"
    output_dir.mkdir(parents=True, exist_ok=True)

    program_screenings = {}

    for iso_day, path in inputs:
        print(f"Parsing {path.name}...")
        html = path.read_text(encoding="utf-8")
        screenings = parse_html_content(html, _parse_iso_date(iso_day))
        if not screenings:
            raise RuntimeError(f"No screenings parsed from {path} (date {iso_day}).")

        for screening in screenings:
            program = screening["program"]
            # Keep the existing grouping behavior from parse_and_group_screenings.py
            if program.startswith("Cannes Classics"):
                program = "Cannes Classics"
            if program.startswith("Cinéma de la Plage"):
                program = "Cinéma de la Plage"
            program_screenings.setdefault(program, []).append(screening)

    header, program_events = create_ics_content(program_screenings)

    for program, events in program_events.items():
        write_program_calendar(header, events, program, output_dir)
        print(f"Created calendar for: {program}")

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

def generate_program_ics_from_sources(date_to_url: Dict[str, str]) -> None:
    # Create output directory if it doesn't exist
    output_dir = BASE_DIR / "calendar_files" / "programs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch & parse each day
    program_screenings = {}

    for iso_day in sorted(date_to_url.keys()):
        url = (date_to_url.get(iso_day) or "").strip()
        if not url:
            continue

        print(f"Fetching {iso_day}...")
        html = fetch_html(url)
        screenings = parse_html_content(html, _parse_iso_date(iso_day))
        if not screenings:
            debug_path = _write_debug_html(iso_day, html)
            raise RuntimeError(
                f"No screenings parsed for {iso_day}. "
                f"This usually means the fetched page isn't the schedule HTML (auth/redirect). "
                f"Saved response to: {debug_path}"
            )

        for screening in screenings:
            program = screening["program"]
            # Keep the existing grouping behavior from parse_and_group_screenings.py
            if program.startswith("Cannes Classics"):
                program = "Cannes Classics"
            if program.startswith("Cinéma de la Plage"):
                program = "Cinéma de la Plage"
            program_screenings.setdefault(program, []).append(screening)

    header, program_events = create_ics_content(program_screenings)

    for program, events in program_events.items():
        write_program_calendar(header, events, program, output_dir)
        print(f"Created calendar for: {program}")

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
    # Preferred behavior: read local HTML dumps from ./html/YYYY-MM-DD.html
    html_dir = BASE_DIR / "html"
    if html_dir.exists():
        generate_program_ics_from_html_dir(html_dir)
        print("All calendar files have been created successfully!")
        raise SystemExit(0)

    # Fallback behavior: fetch from URLs in schedule_sources.py (may be blocked by Cloudflare/auth)
    if not DATE_TO_URL:
        raise SystemExit(
            "No inputs found.\n"
            "- Option A (recommended): create an 'html/' folder and add files like '2025-05-12.html'\n"
            "- Option B: configure DATE_TO_URL in schedule_sources.py"
        )

    generate_program_ics_from_sources(DATE_TO_URL)
    print("All calendar files have been created successfully!")