from urllib.parse import quote_plus

import pandas as pd
from sklearn.cluster import KMeans
from geopy.distance import geodesic

def generate_google_maps_link(addresses_ordered):
    """
     Generate a URL-encoded Google Maps route URL for an ordered list of addresses.

     Args:
         addresses_ordered (list of str): addresses in visiting order.

     Returns:
         str: Google Maps route link.
     """
    base = "https://www.google.com/maps/dir/?api=1"

    # encode each address
    encoded_addresses = [addr.replace(' ', '+') for addr in addresses_ordered]

    origin = encoded_addresses[0]
    destination = encoded_addresses[-1]
    waypoints =  "|".join(encoded_addresses[1:-1]) if len(encoded_addresses) > 2 else ""
    print(f"waypoints={waypoints}")
    url = f"{base}&origin={origin}&destination={destination}"
    if waypoints:
        url += f"&waypoints={waypoints}"
    return url


def cluster_recipients(recipients_df, num_groups):
    """
    Assign each recipient to a geographic cluster using KMeans.

    Args:
        recipients_df (pd.DataFrame): must have columns ['latitude', 'longitude'].
        num_groups (int): number of clusters/groups to form.

    Returns:
        pd.DataFrame: same as input with a new column 'group' (0..num_groups-1).
    """
    coords = recipients_df[['latitude', 'longitude']].values
    kmeans = KMeans(n_clusters=num_groups, random_state=42).fit(coords)
    recipients_df = recipients_df.copy()
    recipients_df['group'] = kmeans.labels_
    #recipients_df = distribute_evenly(df=recipients_df, num_groups=num_groups)
    return recipients_df


def create_distance_matrix(coords):
    """
    Create a symmetric distance matrix (in km) between all points.

    Args:
        coords (list of [lat, lon]): coordinates of points.

    Returns:
        list of list of float: distance matrix.
    """
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
            else:
                matrix[i][j] = geodesic(coords[i], coords[j]).km
    return matrix

def distribute_evenly(df, num_groups):
    """
    Evenly distribute rows into `num_groups` based on latitude sorting.
    Adds a 'group' column with values 0..(num_groups-1).
    """
    df = df.copy()
    df = df.sort_values(by=['latitude', 'longitude']).reset_index(drop=True)

    group_sizes = [len(df) // num_groups] * num_groups
    for i in range(len(df) % num_groups):
        group_sizes[i] += 1  # distribute remainder

    group_labels = []
    for group_id, size in enumerate(group_sizes):
        group_labels.extend([group_id] * size)

    df['group'] = group_labels
    return df


def assign_even_groups(df, num_groups):
    """
    Evenly distribute addresses into `num_groups` while keeping nearby ones together.
    Sorts by latitude and longitude.
    """
    df = df.copy()

    # STEP 1: sort the DataFrame by latitude and longitude
    df = df.sort_values(by=['latitude', 'longitude']).reset_index(drop=True)

    n = len(df)

    # STEP 2: compute how many points go into each group
    group_sizes = [n // num_groups] * num_groups
    for i in range(n % num_groups):   # distribute the remainder
        group_sizes[i] += 1

    # STEP 3: create the group labels
    group_labels = []
    for i, size in enumerate(group_sizes):
        group_labels.extend([i] * size)

    # STEP 4: assign the labels to the DataFrame
    df['group'] = group_labels

    return df


