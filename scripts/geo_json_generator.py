import glob
import json

import yaml


def generate_geo_json():
    geojson = {"type": "FeatureCollection", "features": []}

    # 讀取 locations 目錄下所有 YAML
    for file in glob.glob("content/locations/*.yaml"):
        with open(file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

            works = data if isinstance(data, list) else [data]
            for work in works:
                anime = work.get("anime", "未知作品")
                for loc in work.get("locations", []):
                    lat = loc.get("lat")
                    lon = loc.get("lon")
                    if lat is None or lon is None:
                        continue  # 跳過沒有座標的地點

                    geojson["features"].append(
                        {
                            "type": "Feature",
                            "properties": {
                                "title": loc.get("name", ""),
                                "anime": anime,
                                "visited": loc.get("visited", False),
                                "category": loc.get("category", ""),
                                "notes": loc.get("notes", ""),
                                "date": loc.get("date", ""),
                                "city": loc.get("city", ""),
                                "country": loc.get("country", ""),
                                "tags": loc.get("tags", []),
                            },
                            "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        }
                    )

    with open("output/places.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"生成 GeoJSON，總共 {len(geojson['features'])} 個地點")


if __name__ == "__main__":
    generate_geo_json()
