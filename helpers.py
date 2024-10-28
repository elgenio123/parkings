from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
from openlocationcode import openlocationcode
import numpy as np
import requests
import pandas as pd
from sklearn.neighbors import KernelDensity

def get_best_model(X, max_k=10):
    best_score = -1
    previous_score = -1
    k = 2
    best_model = None

    while k <= max_k:
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(X)
        
        if len(set(labels)) > 1:
            score = silhouette_score(X, labels)
            if score < previous_score:
                break
        
        previous_score = score
        best_model = kmeans
        best_score = score
        k += 1
    
    return best_model, best_score


def get_plus_code(lat, lon):
    # Create an Open Location Code from latitude and longitude
    code = openlocationcode.encode(lat, lon)
    return code



def get_address(lat, lon):
    url = f"http://osm1.lewootrack.com:4000/v1/reverse?point.lat={lat}&point.lon={lon}&size=1` "
    area=''
    region = ''
    country = ''
    county = ''
    town = ''
    try:
        response = requests.get(url)
        data = response.json()
        
        # Pretty-print the JSON data
        # print(json.dumps(data, indent=4))
        
        area = data['features'][0]['properties']['label']
        area_split = area.split(',')[0]
        county = data['features'][0]['properties']['county']
        region = data['features'][0]['properties']['region']
        country = data['features'][0]['properties']['country']
        town = data['features'][0]['properties']['locality']
        
        return f"{area_split}||{county}|{region}|{country}({town})"
    
        
    except KeyError as k:
        #print(f"Key error: {k}")
        return f"{area}||{county}|{region}|{country}({town})"
    except IndexError as e:
        #print(f"IndexError occurred: {e}")
        return f"{area}||{county}|{region}|{country}({town})"
    except Exception as e:
        #print(f"Error occured: {e}")
        return ''

def to_hour(total_minutes):
    
    total_minutes = np.abs(total_minutes)
    # Convert to hours and minutes
    hours = int(total_minutes // 60)
    minutes = (total_minutes % 60)

    # Format the output as "hours:minutes"
    time_formatted = f"{hours}:{int(minutes):02d}:{int((minutes - int(minutes)) * 60):02d}"
    return time_formatted

def compare_first_7_pluscode(df, pluscode_value):

    # Extract the first 7 characters of the pluscodes
    df['pluscode_prefix'] = df['last_pluscode'].str[:7]
    pluscode_prefix = pluscode_value[:7]

    # Count the number of pluscodes that match the first 7 characters
    identical_count = df[df['pluscode_prefix'] == pluscode_prefix].shape[0]

    # Total number of pluscodes
    total_pluscodes = df.shape[0]

    # Calculate and return the ratio
    if total_pluscodes == 0:
        return 0  # To avoid division by zero
    
    return identical_count / total_pluscodes

def get_frequent_parking_interval(car_data, time):
    # Reshape the data for KDE
    car_data = car_data.dropna(subset=[time])
    if car_data[time].empty:
        return (None, None), None
    parking_times = car_data[time].values[:, np.newaxis]
    # print(parking_times)
    # Apply KDE to find the density of parking times
    kde = KernelDensity(kernel='gaussian', bandwidth=30).fit(parking_times)  # Bandwidth controls smoothness
    time_range = np.linspace(0, 1440, 1440)[:, np.newaxis]
    log_density = kde.score_samples(time_range)
    
    # Find the peak (most likely parking time)
    peak_index = np.argmax(log_density)
    peak_time = time_range[peak_index][0]
    
    # Define the interval around the peak (e.g., +/- 60 minutes)
    interval_start = max(peak_time - 60, 0)
    interval_end = min(peak_time + 60, 1440)
    
    # Compute proportion of parking events within this interval
    in_interval = ((car_data[time] >= interval_start) & 
                   (car_data[time] <= interval_end))
    proportion = in_interval.mean()  # Proportion of events in the interval
    
    return (interval_start, interval_end), proportion

def compare_plus_codes(code1, code2, length=4):
    # Convert both codes to strings (handle NaN or non-string types)
    if not isinstance(code1, str):
        code1 = str(code1) if pd.notna(code1) else ''
    if not isinstance(code2, str):
        code2 = str(code2) if pd.notna(code2) else ''
    
    # Extract the first 'length' characters from both codes
    code1_part = code1[:length]
    code2_part = code2[:length]
    
    # Compare and return the result
    return code1_part == code2_part

def get_first_last_ignition(x):
    first_on = x.loc[x['event_flag'] == 1024].nsmallest(1, 'timestamp')
    last_off = x.loc[x['event_flag'] == 4096].nlargest(1, 'timestamp')
    
    return pd.Series({
        'first_ignition_on': first_on['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').values[0] if not first_on.empty else pd.NaT,
        'first_lat': first_on['lat'].values[0] if not first_on.empty else None,
        'first_lon': first_on['lon'].values[0] if not first_on.empty else None,
        'first_pluscode': first_on['pluscode'].values[0] if not first_on.empty else None,
        'last_ignition_off': last_off['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').values[0] if not last_off.empty else pd.NaT,
        'weekday': last_off['weekday'].values[0] if not last_off.empty else None,
        'last_lat': last_off['lat'].values[0] if not last_off.empty else None,
        'last_lon': last_off['lon'].values[0] if not last_off.empty else None,
        'last_pluscode': last_off['pluscode'].values[0] if not last_off.empty else None
    })


