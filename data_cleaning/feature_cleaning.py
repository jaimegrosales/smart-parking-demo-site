# Don't Drop Electric or Accessible because little spots and patterns are hard to catch

# Drop Commuter and Faculty with threshold of 10 -> Figure out if should be dropping all by observing Grace

import pandas as pd
import numpy as np

print("Reading Data", flush=True)
data = pd.read_csv("parking_data-raw.csv")
print("Done Reading Data", flush=True)
# Turn all 3 Zones to 42 and 2 to 41 | Due to JMU Changing Zone Numbers
print(data['Zone'].unique())

data.loc[data['Zone'] == 3, 'Zone'] = 42
data.loc[data['Zone'] == 2, 'Zone'] = 41

print(data['Zone'].unique(), flush=True)


# Method for dropping random 0s
def dropRandomZero(data, threshold, name):
    print(name)

    prev_zero_count = -1 # Initialize to -1 to enter loop
    current_zero_count = (data['Current Availability'] == 0).sum()

    print('\tThreshold: ',threshold)
    print("\tZeros before dropping random:", current_zero_count)
    # Loop to clean all invalid 0s inputted by IOT device
    while prev_zero_count != current_zero_count:
    
        prev_zero_count = current_zero_count   

        data = data.copy()
        data['diff_prev'] = data['Current Availability'].diff().abs()  # Difference from the previous value
        data['diff_next'] = data['Current Availability'].diff(-1).abs()  # Difference from the next value
        data['diff_prev'] = data['diff_prev'].fillna(0)
        data['diff_next'] = data['diff_next'].fillna(0)

        # Drop rows where the value is 0 and the difference with previous or next value is greater than 10
        
        condition = (data['Current Availability'] == 0) & ((data['diff_prev'] > threshold) | (data['diff_next'] > threshold))

        data = data[~condition]

        

        data = data.drop(columns=['diff_prev', 'diff_next'])
        
        current_zero_count = (data['Current Availability'] == 0).sum()

    print("\tZeros after dropping random:", current_zero_count)
    print(data[data['Current Availability'] == 0].head(5), flush=True)
    return data


# Split Data by garage
ballard = data[data['Zone'].isin([29,22,30,27])].copy()
champions = data[data['Zone'].isin([31,13,32,40])].copy()
chesapeake = data[data['Zone'].isin([33,19,34])].copy()
grace = data[data['Zone'].isin([35,4,36,6])].copy()
mason = data[data['Zone'].isin([37,28,12])].copy()
warsaw = data[data['Zone'].isin([38,42,39,41])].copy()

# Ballard
ballard_zones = {
    29: 'Accessible',
    22: 'Commuter',
    30: 'Electric',
    27: 'Faculty'
}
ballard.loc[:, 'Zone Name'] = ballard['Zone'].map(ballard_zones)

bA = ballard[ballard['Zone Name'] == 'Accessible']
bA_cleaned = dropRandomZero(bA, 5, 'Ballard Accessible')
bC = ballard[ballard['Zone Name'] == 'Commuter']
bC_cleaned = dropRandomZero(bC, 10, 'Ballard Commuter')
bE = ballard[ballard['Zone Name'] == 'Electric']
# bE_cleaned = dropRandomZero(bE, 0, 'Ballard Electric')
bF = ballard[ballard['Zone Name'] == 'Faculty']
bF_cleaned = dropRandomZero(bF, 10, 'Ballard Faculty')

ballard_cleaned = pd.concat([bA_cleaned, bC_cleaned, bE, bF_cleaned], axis=0, ignore_index=True)

# Champions
champ_zones= {
    31: 'Accessible',
    13: 'Commuter',
    32: 'Electric',
    40: 'Faculty'
}
champions.loc[:, 'Zone Name'] = champions['Zone'].map(champ_zones)

cA = champions[champions['Zone Name'] == 'Accessible']
cA_cleaned = dropRandomZero(cA, 3, 'Champions Accessible')
cC = champions[champions['Zone Name'] == 'Commuter']
cC_cleaned = dropRandomZero(cC, 10, 'Champions Commuter')
cE = champions[champions['Zone Name'] == 'Electric']
# cE_cleaned = dropRandomZero(cE, 0, 'Champions Electric')
cF = champions[champions['Zone Name'] == 'Faculty']
cF_cleaned = dropRandomZero(cF, 10, 'Champions Faculty')

champions_cleaned = pd.concat([cA_cleaned, cC_cleaned, cE, cF_cleaned], axis=0, ignore_index=True)

# Chesapeake
ches_zones = {
    33: 'Accessible',
    19: 'Commuter',
    34: 'Electric'
}
chesapeake.loc[:, 'Zone Name'] = chesapeake['Zone'].map(ches_zones)

chA = chesapeake[chesapeake['Zone Name'] == 'Accessible']
chA_cleaned = dropRandomZero(chA, 5, 'Chesapeake Accessible')
chC = chesapeake[chesapeake['Zone Name'] == 'Commuter']
chC_cleaned = dropRandomZero(chC, 10, 'Chesapeake Commuter')
chE = chesapeake[chesapeake['Zone Name'] == 'Electric']
# chE_cleaned = dropRandomZero(chE, 3, 'Chesapeake Electric')

chesapeake_cleaned = pd.concat([chA_cleaned, chC_cleaned, chE], axis=0, ignore_index=True)

# Grace
grace_zones = {
    35: 'Accessible',
    4: 'Commuter',
    36: 'Electric',
    6: 'Faculty'
}
grace.loc[:, 'Zone Name'] = grace['Zone'].map(grace_zones)

gA = grace[grace['Zone Name'] == 'Accessible']
gA_cleaned = dropRandomZero(gA, 5, 'Grace Accessible')
gC = grace[grace['Zone Name'] == 'Commuter']
gC_cleaned = dropRandomZero(gC, 10, 'Grace Commuter')
gE = grace[grace['Zone Name'] == 'Electric']
# gE_cleaned = dropRandomZero(gE, 3, 'Grace Electric')
gF = grace[grace['Zone Name'] == 'Faculty']
gF_cleaned = dropRandomZero(gF, 10, 'Grace Faculty')

grace_cleaned = pd.concat([gA_cleaned, gC_cleaned, gE, gF_cleaned], axis=0, ignore_index=True)
gC.to_csv("grace_commuter.csv")

# Mason
mason_zones = {
    37: 'Accessible',
    28: 'Electric',
    12: 'Faculty'
}
mason.loc[:, 'Zone Name'] = mason['Zone'].map(mason_zones)

mA = mason[mason['Zone Name'] == 'Accessible']
mA_cleaned = dropRandomZero(mA, 35, 'Mason Accessible')
mE = mason[mason['Zone Name'] == 'Electric']
# mE_cleaned = dropRandomZero(mE, 3, 'Mason Electric')
mF = mason[mason['Zone Name'] == 'Faculty']
mF_cleaned = dropRandomZero(mF, 10, 'Mason Faculty')

mason_cleaned = pd.concat([mA_cleaned, mE, mF_cleaned], axis=0, ignore_index=True)

# Warsaw
warsaw_zones = {
    38: 'Accessible',
    42: 'Commuter',
    39: 'Electric',
    41: 'Faculty'
}
warsaw.loc[:, 'Zone Name'] = warsaw['Zone'].map(warsaw_zones)

wA = warsaw[warsaw['Zone Name'] == 'Accessible']
wA_cleaned = dropRandomZero(wA, 5, 'Warsaw Accessible')
wC = warsaw[warsaw['Zone Name'] == 'Commuter']
wC_cleaned = dropRandomZero(wC, 10, 'Warsaw Commuter')
wE = warsaw[warsaw['Zone Name'] == 'Electric']
# wE_cleaned = dropRandomZero(wE, 3, 'Warsaw Electric')
wF = warsaw[warsaw['Zone Name'] == 'Faculty']
wF_cleaned = dropRandomZero(wF, 10, 'Warsaw Faculty')

warsaw_cleaned = pd.concat([wA_cleaned, wC_cleaned, wE, wF_cleaned], axis=0, ignore_index=True)

data_cleaned = pd.concat([ballard_cleaned, champions_cleaned, chesapeake_cleaned, grace_cleaned, mason_cleaned, warsaw_cleaned], axis=0, ignore_index=True)


data_cleaned.to_csv("Train_cleaned.csv")

# Confirm Feature List is Complete for Events and can be dropped for others
