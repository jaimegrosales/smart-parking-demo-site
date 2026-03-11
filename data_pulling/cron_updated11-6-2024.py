import requests
import os
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

url = "https://www.jmu.edu/cgi-bin/parking_sign_data.cgi?hash=53616c7465645f5f4c03eadd986acf07775e314a27e46ac7b36f35b8887e4e67ea5489a0733beab3e908f947f1a121913b0c1bbaa8d855d0a76820c2ce3b3b4f9c78a1a4638afe82e66c5e27e2c5af01|869835tg89dhkdnbnsv5sg5wg0vmcf4mfcfc2qwm5968unmeh5"
# warsaw has been changed from 3 to 42
desired_zone_ids = ['22', '13', '19', '4', '42', '27', '40', '12', '6', '41', '30', '32', '34', '36', '28', '39', '29', '31', '33', '35', '37', '38']
zones = {
    '29': 'Ballard Accessible',
    '31': 'Champions Accessible',
    '33': 'Chesapeake Accessible',
    '35': 'Grace Accessible',
    '37': 'Mason Accessible',
    '38': 'Warsaw Accessible',
    '22': 'Ballard Commuter',
    '13': 'Champions Commuter',
    '19': 'Chesapeake Commuter',
    '4': 'Grace Commuter',
    '42': 'Warsaw Commuter',
    '30': 'Ballard Electric',
    '32': 'Champions Electric',
    '34': 'Chesapeake Electric',
    '36': 'Grace Electric',
    '28': 'Mason Electric',
    '39': 'Warsaw Electric',
    '27': 'Ballard Faulty',
    '40': 'Champions Faculty',
    '6': 'Grace Faculty',
    '12': 'Mason Faculty',
    '41': 'Warsaw Faculty'
}
with open('/home/ubuntu/collection/pulling_cron.txt', 'a') as f:
    f.write('Script triggered\n')


# Pull once then terminate and CRON will make run every minute
zone_data = {}

try:
    response = requests.get(url)

    if response.status_code == 200:
        # print(response.text)

        # Parse the XML data
        root = ET.fromstring(response.text)

        for zone_vacancy in root.findall('./ZoneVacanSpaces'):
            zone_id = zone_vacancy.find('ZoneId').text
            # Check if the ZoneId is one of the desired values and not already in the dictionary
            if zone_id in desired_zone_ids and zone_id not in zone_data:
                zone_id_int = int(zone_id)
                as_of = zone_vacancy.find('AsOf').text
                result = int(zone_vacancy.find('Result').text)

                # Add the data to the dictionary
                zone_data[zone_id] = (zone_id_int, as_of, result)

            # Check if the Zoneid is desired and if not send email about 
            if zone_id not in desired_zone_ids:
                message = Mail(
                    from_email='suskojr@dukes.jmu.edu',
                    to_emails=['jacob.susko@gmail.com', 'saund2lr@dukes.jmu.edu', 'margarrx@dukes.jmu.edu',
                                'hudso2tx@dukes.jmu.edu', 'belsarpp@jmu.edu', 'eltawass@jmu.edu'],
                    subject=f'Unexpected Zone {zone_id}',
                    html_content=f'<strong>Recieve unexpected Zone_ID {zone_id}</strong>')
                try:
                    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                    response = sg.send(message)
                    print(response.status_code)
                    print(response.body)
                    print(response.headers)
                except Exception as e:
                    print(e.message)


    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

except requests.exceptions.RequestException as req_error:
    print(f"HTTP request error: {req_error}")

except ET.ParseError as parse_error:
    print(f"XML parsing error: {parse_error}")

# Attempt to connect to the mySQL database
try:
    connection = mysql.connector.connect(
        host='127.0.0.1',
        database='parking_data',
        user='root',
        password='farida96'
    )

    cursor = connection.cursor()

    # Insert the data from the dictionary into the MySQL table
    for zone_id, values in zone_data.items():
        query = "INSERT INTO parking_data (zone_id, as_of, result) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, values)
            # print(f"Data inserted successfully for ZoneId: {zone_id}")
            print(f"Garage {zones[zone_id]} inserted {values[2]} at zone {zone_id}")
        except Error as insert_error:
            # print(f"Error inserting data for ZoneId {zone_id}: {insert_error}")
            print(f"Error inserting data for Garage {zones[zone_id]} with Zoneid {zone_id}: {insert_error}")

    # Commit the changes to the database
    connection.commit()

    cursor.close()
    connection.close()

except Error as mysql_error:
    print(f"MySQL connection error: {mysql_error}")