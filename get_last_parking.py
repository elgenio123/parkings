import pandas as pd
from helpers import get_plus_code, get_address, compare_plus_codes

df = pd.read_csv('parked_cars.csv')
permenent_data = pd.read_excel('permenent_parkings.xlsx')

df['timestamp'] = pd.to_datetime(df['timestamp'])

# Define custom day start and end
start_time = pd.to_datetime('04:00:00').time()
end_time = pd.to_datetime('03:59:59').time()

# Get the last date in the dataset
last_date = df['timestamp'].dt.date.max()

# Create a custom date range for filtering
custom_day_start = pd.Timestamp.combine(last_date, start_time)
custom_day_end = pd.Timestamp.combine(last_date + pd.Timedelta(days=1), end_time)

# Filter the DataFrame for the custom day
filtered_df = df[(df['timestamp'] >= custom_day_start) & (df['timestamp'] <= custom_day_end)]

# Get the last parking data for each car
last_parking_data = filtered_df.sort_values('timestamp').groupby('unique_id').last().reset_index()


columns_to_keep = ['unique_id', 'lat', 'lon', 'timestamp']

# Drop columns that are not in columns_to_keep
last_parking_data_filtered = last_parking_data[columns_to_keep]

last_parking_data_filtered['pluscode'] = last_parking_data_filtered.apply(lambda row: get_plus_code(row['lat'], row['lon']), axis=1)

last_parking_data_filtered['last_parking_location'] = last_parking_data_filtered.apply(lambda row: get_address(row['lat'],row['lon']) if pd.notna(row['lat']) or pd.notna(row['lon']) else '', axis=1)
last_parking_data_filtered = last_parking_data_filtered.rename(columns={'pluscode': 'last_parking_pluscode', 'timestamp': 'last_parking_time'})
last_parking_data_filtered.to_csv('last_parking_data.csv')

res = permenent_data.merge(last_parking_data_filtered, how='left', on='unique_id', suffixes=('', '_first'))
res = res.drop(columns=['lat', 'lon', 'longitude', 'latitude'])

res['temp_location'] = res.apply(lambda row: None if (row['location'] == row['last_parking_location'] and compare_plus_codes(row['pluscode'], row['last_parking_pluscode'])) else 'Different', axis=1)
res.to_excel('permenent_parkings_new.xlsx')