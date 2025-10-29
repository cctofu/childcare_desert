import json
from pathlib import Path
import pandas as pd
import geopandas as gpd
import folium
import sys
import colorful as cf

def norm_zip(z):
    s = "".join(ch for ch in str(z) if ch.isdigit())
    return s[:5].zfill(5) if s else None

if __name__ == "__main__":
    json_path = Path(sys.argv[1])
    zcta_path = Path(sys.argv[2])

    if not json_path.exists():
        print(f"Error: JSON file '{json_path}' not found.")
        sys.exit(1)
    if not zcta_path.exists():
        print(f"Error: shapefile '{zcta_path}' not found.")
        sys.exit(1)

    output_name = json_path.stem + ".html"
    output_path = Path("./outputs") / output_name
    geo = gpd.read_file(zcta_path)
    geo["ZCTA5CE10"] = geo["ZCTA5CE10"].astype(str).str.zfill(5)

    with json_path.open() as f:
        obj = json.load(f)
    zip_list = sorted({z for z in obj if z})
    covered = pd.DataFrame({"zip": zip_list})


    in_ny = geo["ZCTA5CE10"].between("00501", "14925")
    geo["in_dataset_extent"] = in_ny
    geo["covered"] = geo["ZCTA5CE10"].isin(covered["zip"])

    m = folium.Map(location=[42.9, -75.0], zoom_start=6, tiles="cartodbpositron")
    def style_fn(feat):
        props = feat["properties"]
        cov = bool(props.get("covered"))
        if cov:
            return {"fillColor": "#2ca25f", "color": "#444444", "weight": 0.3, "fillOpacity": 0.65}
        else:
            return {"fillColor": "#d9d9d9", "color": "#aaaaaa", "weight": 0.2, "fillOpacity": 0.5}
    folium.GeoJson(
        geo.to_json(),
        name="NY ZIP coverage",
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["ZCTA5CE10", "in_dataset_extent", "covered"],
            aliases=["ZIP", "In dataset extent", "Covered"],
            localize=True,
        ),
    ).add_to(m)
    folium.LayerControl().add_to(m)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))
    print(cf.seaGreen(f"Saved map → {cf.bold(cf.yellow(output_path))}"))
