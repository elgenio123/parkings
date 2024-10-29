import pandas as pd
from helpers import get_first_last_ignition

print('Modules imported successfully')

print('Loading data...')
chunk_size = 500000  # Number of rows per chunk
all_data = []
for chunk in pd.read_csv('../parking_data.csv', chunksize=chunk_size):
    chunk = chunk[['uniqueid', 'lat', 'lng', 'pluscode',  'event_flag', 'created_on', 'isha','ishb']]
    chunk = chunk.rename(columns={'uniqueid': 'unique_id', 'created_on': 'timestamp', 'lng': 'lon'})
    all_data.append(chunk)

value_counts_list = [df['unique_id'].value_counts() for df in all_data]

# Step 2: Concatenate the value counts of all DataFrames
combined_counts = pd.concat(value_counts_list)

# Step 3: Group by the CarID and sum the counts
total_counts = combined_counts.groupby(combined_counts.index).sum()
print(f"Data on {len(total_counts)} cars loaded")

print('Geting cars with event flag 1024 and 4096 and lat, lon different from 0 ...')
parked_car_data = pd.DataFrame()
for i in range(len(all_data)):
    data = all_data[i]
    # Filter the data for emissions
    data = data[((data['event_flag'] == 1024) | (data['event_flag'] == 4096)) &(data['lat'] != 0) & (data['lon'] != 0)]
    parked_car_data = pd.concat([parked_car_data, data], ignore_index=True)
# parked_car_data.head()
counts = parked_car_data['unique_id'].value_counts()
print(f"{len(counts)} car data")

print('Data processing...')
parked_cars = pd.DataFrame()
for i in range(len(all_data)):
    data = all_data[i]
    # Filter the data for emissions
    data = data[( (data['event_flag'] == 4096)) &(data['lat'] != 0) & (data['lon'] != 0)]
    parked_cars = pd.concat([parked_cars, data], ignore_index=True)
parked_cars.head()
parked_cars.to_csv('parked_cars.csv')

left_cars = pd.DataFrame()
for i in range(len(all_data)):
    data = all_data[i]
    # Filter the data for emissions
    data = data[data['event_flag'] == 1024  & (data['lat'] != 0) & (data['lon'] != 0)]
    parked_cars = pd.concat([parked_cars, data], ignore_index=True)
left_cars.to_csv('left_cars.csv')

parked_car_data['timestamp'] = pd.to_datetime(parked_car_data['timestamp'])

print("Getting first ignition on and last igition off of each car everyday...")
# Shift time by 4 hours backwards to define a custom day
parked_car_data['custom_day'] = parked_car_data['timestamp'] - pd.Timedelta(hours=4)

parked_car_data['weekday'] = parked_car_data['custom_day'].dt.day_name()

# Group by car ID and custom day
parked_car_data['custom_day'] = parked_car_data['custom_day'].dt.date
grouped = parked_car_data.groupby(['unique_id', 'custom_day'])

# Apply function to get results
result = grouped.apply(get_first_last_ignition).reset_index()
print("Succeeded")

print("Loading pluscodes table")
pluscodes = pd.read_csv('../location.csv', on_bad_lines='skip')
pluscodes.columns = ['plucode', 'location', 'none', 'timestamp']
pluscodes = pluscodes.drop(columns=['none', 'timestamp'])

result = pd.merge(result, pluscodes, left_on='first_pluscode', right_on='plucode' ,how='left')
result = pd.merge(result, pluscodes, left_on='last_pluscode', right_on='plucode', how='left')

result = result.drop(columns=['plucode_x', 'plucode_y'])
result = result.rename(columns={'location_x': 'first_location', 'location_y': 'last_location'})

duplicate_counts = result['unique_id'].value_counts()

print(f"Ignititon on and off for {len(duplicate_counts)} cars gotten")

result.to_excel('results.xlsx')