import requests
import time
import pandas as pd

def geocode_address(address, api_key):
    """
    Geocode a single address using Google Maps API.
    """
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': address, 'key': api_key}
    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        print(f"⚠️ Failed to geocode: {address} — {data['status']}")
        return None, None


def geocode_missing_and_save(df, api_key, address_col='address', lat_col='latitude', lon_col='longitude',
                             output_file='output.xlsx', sheet_name='address'):
    """
    Geocode only rows where lat/lon are missing, then save updated DataFrame.
    """
    df = df.copy()  # don’t modify original
    updated = False

    if lat_col not in df.columns:
        df[lat_col] = pd.NA
    if lon_col not in df.columns:
        df[lon_col] = pd.NA
    indices_to_drop = []  # keep track of rows to drop
    for idx, row in df.iterrows():
        if pd.isna(row[lat_col]) or pd.isna(row[lon_col]):

            address = row[address_col]
            if pd.notna(address):
                address = address + " אריאל "
            print(f"🌎 Geocoding: {address}")
            lat, lon = geocode_address(address, api_key)

            if lat is not None and lon is not None:
                df.at[idx, lat_col] = lat
                df.at[idx, lon_col] = lon
                updated = True
            else:
                print(f"⚠️ Could not geocode: {address}")
                indices_to_drop.append(idx)
            time.sleep(0.1)  # be nice to API


    if indices_to_drop:
        df.drop(index=indices_to_drop, inplace=True)

    if updated:
        df.to_excel(output_file, index=False,sheet_name=sheet_name)
        print(f"\n✅ Updated file saved to: {output_file}")
    else:
        print("\nℹ️ No missing lat/lon found — nothing updated.")

    return df



def get_optimized_address_order(addresses, api_key):
    """
    Calls Google Directions API to reorder the given addresses for shortest route.

    Args:
        addresses (list of str): full address strings
        api_key (str): your Google Maps API key

    Returns:
        list of str: addresses reordered by Google's optimized route
    """
    if len(addresses) < 3:
        return addresses  # not enough to optimize

    origin = addresses[0]
    destination = addresses[-1]
    waypoints = addresses[1:-1]

    endpoint = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "waypoints": "optimize:true|" + "|".join(waypoints),
        "key": api_key
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    if data["status"] != "OK":
        raise RuntimeError(f"Google API error: {data['status']} - {data.get('error_message', '')}")

    order = data["routes"][0]["waypoint_order"]

    optimized = [origin] + [waypoints[i] for i in order] + [destination]
    return optimized