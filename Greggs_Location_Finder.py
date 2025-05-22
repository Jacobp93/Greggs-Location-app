import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import OpenCage
from sklearn.neighbors import NearestNeighbors

geolocator = OpenCage(api_key=st.secrets["opencage"]["api_key"])

@st.cache_data
def load_data():
    df = pd.read_excel("Greggs_Locations.xlsx")
    df = df.dropna(subset=['address.latitude', 'address.longitude'])
    df['latitude'] = pd.to_numeric(df['address.latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['address.longitude'], errors='coerce')
    return df

@st.cache_data
def get_geocode(postcode):
    return geolocator.geocode(postcode)

def find_nearest_locations(target_location, data, radius=10):
    if data.empty:
        return pd.DataFrame()
    target_coords = np.radians([[target_location.latitude, target_location.longitude]])
    data_coords = np.radians(data[['latitude', 'longitude']].values.astype(float))
    nbrs = NearestNeighbors(radius=radius * 1609.34, algorithm='ball_tree', metric='haversine')
    nbrs.fit(data_coords)
    distances, indices = nbrs.radius_neighbors(target_coords)
    results = []
    for dist_list, idx_list in zip(distances, indices):
        dist_miles = dist_list * 6371 * 0.621371
        within_radius = [(dist, idx) for dist, idx in zip(dist_miles, idx_list) if dist <= radius]
        top_5 = sorted(within_radius, key=lambda x: x[0])[:5]
        nearest_data = data.iloc[[idx for _, idx in top_5]].copy()
        nearest_data['Distance (miles)'] = [dist for dist, _ in top_5]
        nearest_data = nearest_data[['shopName', 'address.postCode', 'Distance (miles)']]
        results.append(nearest_data)
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# Streamlit UI
st.title("Greggs Location Finder")
st.write("Find the 5 closest Greggs locations by entering a postcode.")

st.sidebar.title("Read Me")
st.sidebar.info(
    "This is a replicated version of my sales event tool.\n\n"
    "It uses OpenCage's geolocation API and algorithms in Python to calculate proximity.\n\n"
    "The original version used by Sales includes customer data, so this version uses Greggs locations instead as a fun example project.\n\n"
    "The idea is to enter a prospect's postcode, name or id to return a short list of nearby customers displaying their products & customer tenure to support social proof selling.\n\n"
    "Try entering any UK Postcode"
)

data = load_data()

postcode = st.text_input("Enter a postcode:", "")
radius = st.slider("Set Search Radius (in miles)", min_value=1, max_value=50, value=10)
search_button = st.button("Search")

if search_button:
    location = get_geocode(postcode)
    if location:
        nearest = find_nearest_locations(location, data, radius)
        if not nearest.empty:
            st.write(f"Top 5 closest Greggs locations within {radius} miles:")
            st.table(nearest)
        else:
            st.warning("No locations found within that radius.")
    else:
        st.error("Invalid postcode.")