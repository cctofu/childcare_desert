'''
UTILITY FUNCTIONS
'''
import pandas as pd
import math

'''
Ensure zipcode is 5 digits, trim to 5 if longer than 5
'''
def normalize_zip(z):
    """
    Ensure ZIP is a 5-digit string, preserving leading zeros.
    """
    s = str(z).strip()
    if not s:
        return None
    # If it's longer than 5 (e.g., ZIP+4), truncate to 5
    if len(s) > 5:
        s = s[:5]
    # Zero-pad if numeric and shorter than 5
    if s.isdigit() and len(s) < 5:
        s = s.zfill(5)
    return s

'''
Load data path and make dataframe
'''
def load_csv(path, zip_col):
    df = pd.read_csv(path)
    df = df.copy()
    df[zip_col] = df[zip_col].map(normalize_zip)
    df = df.dropna(subset=[zip_col])
    return df

def _haversine_miles(lat1, lon1, lat2, lon2):
    _MILES_PER_RAD = 3958.7613 
    p = math.pi / 180.0
    lat1, lon1, lat2, lon2 = lat1*p, lon1*p, lat2*p, lon2*p
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    return 2 * _MILES_PER_RAD * math.asin(math.sqrt(a))