import pandas as pd
from sklearn.preprocessing import StandardScaler
from helpers import get_address, get_best_model, get_plus_code, compare_first_7_pluscode

print('Modules imported successfully')

df = pd.read_excel('results.xlsx')

res = pd.DataFrame()
# Loop through each vehicle ID that has more than 100 rows
i=0
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
vehicles_with_enough_data = df.groupby('unique_id').filter(lambda x: (x['last_lat'].notna() & x['last_lon'].notna()).sum() >= 50)['unique_id'].unique()

print('Computing permanent parkings')

for vehicle_id in vehicles_with_enough_data:

    vehicle1 = df[df['unique_id']==vehicle_id].dropna(subset=['last_lat', 'last_lon'])
    
    # Create a list to hold the DataFrames for each day
    day_vehicles = [vehicle1[vehicle1['weekday'] == day].copy() for day in days_of_week]
    print(f"Vehicule {i}")
    for vehicle_data in day_vehicles:
        # Filter the dataset for the current vehicle
        # print("   Vehicles day")
        vehicle_data['last_ignition_off'] = pd.to_datetime(vehicle_data['last_ignition_off'])
        vehicle_data['hour'] = vehicle_data['last_ignition_off'].dt.hour
        vehicle_data['minute'] = vehicle_data['last_ignition_off'].dt.minute
        vehicle_data['time_left'] = vehicle_data['hour'] * 60 + vehicle_data['minute']

        vehicle_data['first_ignition_on'] = pd.to_datetime(vehicle_data['first_ignition_on'])
        vehicle_data['hour'] = vehicle_data['first_ignition_on'].dt.hour
        vehicle_data['minute'] = vehicle_data['first_ignition_on'].dt.minute
        vehicle_data['time_in_minutes'] = vehicle_data['hour'] * 60 + vehicle_data['minute']
    
        vehicle_data = vehicle_data.drop(columns=['hour', 'minute'])
        coords = vehicle_data[['last_lat', 'last_lon']]
        #print(len(vehicle_data))
        
        # Scale the data (standardize latitudes and longitudes)
        scaler = StandardScaler()
        coords_scaled = scaler.fit_transform(coords)
        
        #train the model
        best_model, best_score = get_best_model(coords_scaled, 5)
        # print(f"Silouhette score: {best_score}")
        
        #get the first row belonging to the max cluster
        vehicle_data['cluster'] = best_model.labels_
        cluster_counts = vehicle_data['cluster'].value_counts().sort_index()
        most_parked_cluster = vehicle_data[vehicle_data['cluster']==cluster_counts.idxmax()].iloc[0]
        #print(vehicle_data)
        
        #neccesary data
        most_parked_cluster = most_parked_cluster[['unique_id', 'weekday']]
        # print(most_parked_cluster)
        
        #get the center of the cluster having the maximum number of points
        cluster_counts = vehicle_data['cluster'].value_counts().sort_index()
            
        # Find the cluster with the maximum number of points
        max_cluster = cluster_counts.idxmax()
        cluster_centers = scaler.inverse_transform(best_model.cluster_centers_)
        max_cluster_center = cluster_centers[max_cluster]

        data = pd.DataFrame()
        
        data['unique_id'] = most_parked_cluster[['unique_id']]
        data['weekday'] = vehicle_data['weekday'].iloc[0]
        
        data['longitude'] = max_cluster_center[1]
        data['latitude']= max_cluster_center[0]
        # data['time']= to_hour(max_cluster_center[2])
        pluscode =  get_plus_code(max_cluster_center[0], max_cluster_center[1])
        data['pluscode']= pluscode
        data['rate'] =  compare_first_7_pluscode(vehicle_data, pluscode)
        # Concatenate DataFrames vertically
        res = pd.concat([data, res], ignore_index=True)
    i += 1
    
res['location'] = res.apply(
    lambda row: get_address(row['latitude'], row['longitude']) 
    if pd.isna(row['location']) or '||||()' in row['location'] and pd.notna(row['latitude']) and pd.notna(row['longitude']) 
    else row['location'], axis=1
)
res.to_excel('permenent_parkings.xlsx', index=False)

print('Saved in permenent_parkings.xlsx file')

