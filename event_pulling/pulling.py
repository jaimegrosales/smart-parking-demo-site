import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# Need to get a new Cookie every few days for running
# Google, inspect, network tab, reload, copy headers

# Function to get events for a specific week
def fetch_events(start_date):
    url = "https://ems.jmu.edu/MasterCalendar/MasterCalendar.aspx/ReloadCalendar"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json; charset=UTF-8",
        "cookie": "_gcl_au=1.1.889559720.1767292995; _fbp=fb.1.1767292995008.229517871556707576; __adroll_fpc=391a8623ad1a1e166bc0f01bbf010e1e-1767292995127; _ga_XZLGFJC3JY=GS2.1.s1771082518$o1$g1$t1771082695$j60$l0$h0; _ga_3QPEZ8YC31=GS2.1.s1771082518$o1$g1$t1771082695$j60$l0$h0; _scid=HxAWqD36RMSqqw3ASiVK80ol0iyW-d1e; _sctr=1%7C1771045200000; _ga=GA1.2.2082831689.1767292995; _scid_r=KpAWqD36RMSqqw3ASiVK80ol0iyW-d1eBR1XNA; _ga_VDJD052M5K=GS2.1.s1771091382$o4$g1$t1771091388$j54$l0$h0; ASP.NET_SessionId=d5mckpqkmwwiqliz5uovhyx0; __AntiXsrfToken=afa236c50dd94534948fefee878db084",
        "origin": "https://ems.jmu.edu",
        "priority": "u=1, i",
        "referer": "https://ems.jmu.edu/MasterCalendar/MasterCalendar.aspx?jmu_redir=r_master-calendar",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    payload = json.dumps({
        "startDate": start_date.strftime("%m/%d/%Y"),
        "displayView": '1',
        "displayFormat": '1',
        "eventTypeIds": '-1',
        "locationIds": '-1',
        "sublocationIds": '',
        "departmentIds": '-1',
        "TZOffset": '0',
        "TZAbbr": '',
        "TZID": '0',
        "keyword": ''
    })

    # Make the request
    response = requests.post(url, headers=headers, data=payload)

    # Print response status and content
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:500]}")  # Print first 500 chars to check content

    if response.status_code == 200:
        print(response.text)  # Instead of just checking "d"

        try:
            return json.loads(response.json()["d"])
        except json.JSONDecodeError:
            print("Error: Response is not valid JSON. Check if session has expired.")
            return []
    else:
        print(f"Failed to fetch events for {start_date}. Status code: {response.status_code}")
        return []    

# Function to parse the event data | adjust => may only look for those marked as isspecial: true
def parse_events(json_data):
    events = []

    # Iterate over each event
    for day_data in json_data:
        event_date = day_data.get("EventDate")
        for event in day_data.get("Events", []):
            event_info = {
                "Event ID": event.get("Id"),
                "Title": event.get("Title"),
                "Description": event.get("Description"),
                "Event Type": event.get("EventType"),
                "Event DateTime": event.get("EventDateTime", {}).get("EventDateTime"),
                "Duration (min)": event.get("EventDateTime", {}).get("EventDuaration"),
                "Location": event.get("Location", {}).get("Name"),
                "Special?": event.get("isSpecial")
            }
            events.append(event_info)
    
    return events


# Main function to fetch events for multiple weeks and save to CSV
def collect_event_data(start_date, num_weeks):
    all_events = []
    
    # Loop over the specified number of weeks
    for i in range(num_weeks):
        # Calculate the start date for the current week
        current_start_date = start_date + timedelta(weeks=i)

        # Fetch events for this week
        json_data = fetch_events(current_start_date)
        
        # Parse the JSON data and add to list
        weekly_events = parse_events(json_data)
        all_events.extend(weekly_events)

    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(all_events)
    df.to_csv("calendar_events-full.csv", index=False)
    print(f"Data saved to calendar_events.csv")

# Run the script
if __name__ == "__main__":
    # Define the starting date for fetching events (e.g., 6 weeks ago)
    start_date = datetime.strptime("02/20/2024", "%m/%d/%Y") # first day of data collected
    
    # Number of weeks to fetch
    num_weeks = 80  # Fetch data for 8 weeks

    # Collect event data and save to CSV
    collect_event_data(start_date, num_weeks)
    # fetch_events(start_date)