# smart-parking-capstone

## sql-to-csv.py
- This code takes a .sql file and converts it into a .csv for easier use in machine learning
- Backup data is pulled as a .sql

## Correlation
- The code in this folder will generate heat matrix for the different garages to be able to see correlations
- The individual spot named files will also generate line graphs, so you can see when each garage begins to fill for each individual spot type
- To run this code you will need to pull a backup of the database to the folder, change the name of the sql file to match in the code then the code will run

## data_pulling
- cron_updated_11-6-2024.py
    - This file runs on the cloud and local server and pulls data from the JMU Parking API and stores it into the database located on these servers
    - This code will not run unless on these servers due to enviornmental set ups such as the email notifications and the database
    
## data_cleaning
- The code in this folder will clean the data to remove all corrupted data including unexpected highs and lows

## ensemble_ML
- This folder includes code to test the full ensemble model (ensemble_fast.py), and to test the ensemble model on future data
- The subfolders have code and instructions for creating, and testing the sub-datasets and sub-models

## feature_list
- The code in this folder is used to perform the feature engineering for all the models
    1. Timestamp conversion to Month, Day of Week, Cyclic Timing

## future_testing
- This folder has code to run the future_testing and instructions on how to run and perform future testing

## event_pulling
- The code in this folder will pull events from JMU Master Calendar, clean the data and make it mergable with feature lists
- pulling.py
    1. To run this code you must first go to JMU Master Calendar website and obtain a cookie and paste it into the code
    2. Then you must specify a start date (Sunday of week) and how many weeks after that you also want to pull and then you can 
    3. run the code
- specialEvents.py
    - This code takes the pulled events and filters so only events labeled 'special' (affect parking) are taken
- make_event_mergable.py
    - This code takes the pulled and filtered events and makes it so they are mergable with a feature list

## Machine_Learning
- The generate_data folder contains different python files to generate different feature lists from the first testing batch
- The other folders contain different ML Models that can be tested with different features by changing what feature list (.csv) is imported at the beginning of the file
- The final_models subfolder contains the code to evaluate models and creating the final knn, lstm, and rfr machine learning models

## garage_graph
- This Google Colab file creates graphs based on a sql file input and will display weekly graphs from a starting date for each day of the week. It will take the data imputed and parse it creating a dataframe for useful information such as the day of the week. Graphs have a set way of being made and can be tweaked to showcase information that needs to be shown.

- Set-Up and Configuration:
    1. Collecting Data:
        a. First connect to the ec2 instance either through the console for the aws account or command in a command line and having the required pem file in order to access the         
        instance.
        b. When successfully connected navigate to the backups folder (cd collections/backup) and identify the most recent data.
        c. Once identified the desired data execute an scp command to download the sql file.
    2. Inputting the Data:
        a. In the .ipynd file select the files icon and upload the recently acquired sql file. Change the sql_file = ‘’ to be the name of the file you had uploaded.
        b. You should now be able to run the script and be able to output graphs.
    3. Configuration Guide:
        a. The following will display what changes aspects on the graphs in order to get the desired displayed data.
            i. plt.ylim(a, b) is how much of the y axis is shown on the graph with a being the lowest you want to see and b being the highest.
            ii. plt.figure will adjust how the graph looks in regards to the space on the x axis. 
            iii. plt.xticks is to select a time set to see data the following is an example (pd.date_range('09:00', '14:00', freq='H'), [f'{hour:02d}:00' for hour in range(9,15)]) what                  this does it limit the graph x axis to only be from 9am to 2pm timeframe




## smart_parking
- The code in this project is for the Flutter app. The app allows users to view the live parking spot count, create an account, and navigate using google maps. Features such as event tracker, traffic tracker, and destination based lists are on track to be completed next semester.
- The app's dart code can be found in smart_parking/lib.
    - main.dart, file that builds that app
    - firebase_options.dart, file that contains API keys for different platforms, in support of the account feature
    - src folder, premade code created when the flutter project was created
    - services folder, code outlining the functionality of the account feature
    - homepage folder, the folder containing the app pages in some case broken with 1 page broken into multiple files for readability
- To run this project,
    1. To run this code on any machine copy smart_parking onto a local computer and run main.dart. This will run the app in a selected web browser.
    2. To run this code in a simulator mode:
        1. Copy smart_parking on to a device running Mac OS
        2. Download Xcode
        3. Run "open -a simulator" in the terminal
        4. Run "run flutter" (Make sure you are in the "ios" folder when running command)
      
## APPAPI
- This folder contains 2 files.
    1. apiPopulator, this script populates the rest api with accurate parking data
    2. appAPI.py, this code defines the rest api and the related html methods
- To run this code:
    - apiPopulator, this code can be run sucussesfully using python 3 on any device as long as the appAPI is running.
    - appAPI.py, this code must be run in a flask environment, and uses gunicorn to bind the api to a port on the machine
