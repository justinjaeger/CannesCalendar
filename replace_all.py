import os
from replace_calendar_events import replace_calendar_events

# Map of program names to their calendar IDs
PROGRAM_CALENDARS = {
    # 'Acid.ics': 'd4d5dd2cefbfa2c15a1482da6957de7b8f7903b1c871c0fa36af188a0db2c81e@group.calendar.google.com',
    # 'Semaine_de_la_Critique.ics': 'f632f19554cfb9a67044ad883666ddab4643f08bc778e83a2d0190e29e5bfff9@group.calendar.google.com',
    'Directors_Fortnight.ics': 'ec5c3f102586cd3fecd8696bf0d33b8479945edbd9f6d85bb61e4cfd5ceb2d58@group.calendar.google.com',
    'In_Competition_-_Feature_Films.ics': 'e7c7aa0ec5a72099675958509fd2f508f4ebd58bb5d6bd1543fbc8eb4af994ad@group.calendar.google.com',
    'Out_of_Competition_-_Midnight_Screenings.ics': '2fef617dbc4934eb290c037b2aca4e4d40cc31496c0726604e129f5f2f1a1389@group.calendar.google.com',
    'Out_of_Competition.ics': '322f266848f0ef6f5689c2c1b9a352dd595cdec4cd0ead39dcf7f9ec0c562a5f@group.calendar.google.com',
    'Cannes_Premiere.ics': 'a347f278133b65f1a7ff5f1645bf0f053755b7ed451ba1e3f126cac9249618d4@group.calendar.google.com',
    'Special_Screenings.ics': '875d34a49e3a02e609fbe5d072097b10d800facf2275166c41a61ef241a4c862@group.calendar.google.com',
    'Un_Certain_Regard.ics': 'ac830df14a2a2a0725f3ffe71f96cb697b65ae10350c1a37024b4405342d6668@group.calendar.google.com',
    'Cannes_Classics.ics': 'fb6788abc4b658f6a4f94803c5f04393d4b761eb4f2daa1688965eb38e769962@group.calendar.google.com',
    'Cinéma_de_la_Plage.ics': '83f6b7cc0de9ac89398c4f147db4fa854b6bea9e2e258cf20dff0c28f347457f@group.calendar.google.com',
    'Cannes_Cinéma.ics': 'fb6788abc4b658f6a4f94803c5f04393d4b761eb4f2daa1688965eb38e769962@group.calendar.google.com',
    'Other.ics': 'aac1105e51979e58b6bacd72e53c592372ad2ca8d95d14b9f53519a98f0c3d04@group.calendar.google.com'
}

def main():
    print("Starting calendar replacement for all programs...")
    print("-" * 50)
    
    for program, calendar_id in PROGRAM_CALENDARS.items():
        ics_path = os.path.join('calendar_files', 'programs', program)
        if not os.path.exists(ics_path):
            print(f"Warning: ICS file not found for {program}, skipping...")
            continue
            
        print(f"\nProcessing {program}...")
        print(f"Calendar ID: {calendar_id}")
        try:
            replace_calendar_events(calendar_id, ics_path)
        except Exception as e:
            print(f"Error processing {program}: {str(e)}")
            continue
            
    print("\nAll programs processed!")

if __name__ == '__main__':
    main() 