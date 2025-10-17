import json
from pathlib import Path
import pandas as pd
import geopandas as gpd
import folium

path = Path("./outputs/has_zipcodes_2.json")
zcta_path = "./cb_2018_us_zcta510_500k/cb_2018_us_zcta510_500k.shp"

def norm_zip(z):
    s = "".join(ch for ch in str(z) if ch.isdigit())
    return s[:5].zfill(5) if s else None

if __name__ == "__main__":
    # --- Load ZCTA polygons (US-wide) ---
    geo = gpd.read_file(zcta_path)
    geo["ZCTA5CE10"] = geo["ZCTA5CE10"].astype(str).str.zfill(5)

    # --- Load your dataset of covered ZIPs (union) ---
    with path.open() as f:
        obj = json.load(f)
    zip_list = obj
    zip_list = sorted({z for z in zip_list if z})
    covered = pd.DataFrame({"zip": zip_list})

    # --- Define your dataset extent (NY ZCTA range); everything else = 'not part of dataset' ---
    in_ny = geo["ZCTA5CE10"].between("00501", "14925")
    geo["in_dataset_extent"] = in_ny

    # Mark covered (only matters inside the dataset extent)
    geo["covered"] = geo["ZCTA5CE10"].isin(covered["zip"])

    # --- Folium map ---
    m = folium.Map(location=[42.9, -75.0], zoom_start=6, tiles="cartodbpositron")

    def style_fn(feat):
        props = feat["properties"]
        cov = bool(props.get("covered"))
        if cov:
            # Covered -> GREEN
            return {"fillColor": "#2ca25f", "color": "#444444", "weight": 0.3, "fillOpacity": 0.65}
        else:
            # In dataset but not covered -> GRAY
            return {"fillColor": "#d9d9d9", "color": "#aaaaaa", "weight": 0.2, "fillOpacity": 0.5}

    folium.GeoJson(
        geo.to_json(),
        name="NY ZIP coverage",
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["ZCTA5CE10", "in_dataset_extent", "covered"],
            aliases=["ZIP", "In dataset extent", "Covered"],
            localize=True
        ),
    ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save("ny_zipcode_2.html")
