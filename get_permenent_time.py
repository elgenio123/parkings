
import pandas as pd
from helpers import get_frequent_parking_interval, to_hour

vehicle = pd.read_excel('results.xlsx')
vehicle['last_ignition_off'] = pd.to_datetime(vehicle['last_ignition_off'])
vehicle['hour'] = vehicle['last_ignition_off'].dt.hour
vehicle['minute'] = vehicle['last_ignition_off'].dt.minute
vehicle['time_parked'] = vehicle['hour'] * 60 + vehicle['minute']

vehicle['first_ignition_on'] = pd.to_datetime(vehicle['first_ignition_on'])
vehicle['hour'] = vehicle['first_ignition_on'].dt.hour
vehicle['minute'] = vehicle['first_ignition_on'].dt.minute
vehicle['time_left'] = vehicle['hour'] * 60 + vehicle['minute']

vehicle = vehicle.drop(columns=['hour', 'minute'])

results = pd.DataFrame(columns=['unique_id', 'weekday', 'interval_parked', 'proportion_parked','interval_left', 'proportion_left'])

# Loop over each car and each day of the week to compute the interval and proportion
for car_id in vehicle['unique_id'].unique():
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        car_day_data = vehicle[(vehicle['unique_id'] == car_id) & (vehicle['weekday'] == day)]
        
        if not car_day_data.empty:
            # Get the frequent parking interval and proportion
            interval_parked, proportion_parked = get_frequent_parking_interval(car_day_data, 'time_parked')
            interval_left, proportion_left = get_frequent_parking_interval(car_day_data, 'time_left')
            
            # Convert the interval to HH:MM format
            if interval_parked[0] is not None:
                interval_hours_parked = (to_hour(interval_parked[0]), to_hour(interval_parked[1]))
            else:
                interval_hours_parked = (None, None)
            if interval_left[0] is not None:
                interval_hours_left = (to_hour(interval_left[0]), to_hour(interval_left[1]))
            else:
                interval_hours_left = (None, None)
           
            
            # Create a new row
            new_row = pd.DataFrame({
                'unique_id': [car_id],
                'weekday': [day],
                'interval_parked': [interval_hours_parked],
                'proportion_parked': [proportion_parked],
                'interval_left' : [interval_hours_left],
                'proportion_left' : [proportion_left]
            })
            
            # Use pd.concat to add the new row to results
            results = pd.concat([results, new_row], ignore_index=True)
        else:
            # Append empty result if no data available for this day
            empty_row = pd.DataFrame({
                'unique_id': [car_id],
                'weekday': [day],
                'interval_parked': [(None, None)],
                'proportion_parked': [None]
            })
            # Use pd.concat to add the empty row to results
            results = pd.concat([results, empty_row], ignore_index=True)

results.to_excel('permenent_time.xlsx')
parked_cars = pd.read_excel('permenent_parkings_new.xlsx')

final_data = pd.merge(results, parked_cars, on=['unique_id', 'weekday'], how='left')
final_data.to_excel('final_data.xlsx')
print("Saved in final_data.xlsx")
