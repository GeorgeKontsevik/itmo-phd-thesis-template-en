#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
REPO_DIR = PACKAGE_DIR.parents[2]
EQUATORIAL_DIR = REPO_DIR / "equatorial"
DEFAULT_OUT = PACKAGE_DIR / "data/equator_belt_map_data.gpkg"
DEFAULT_MANIFEST = PACKAGE_DIR / "data/equator_belt_map_data_manifest.json"

sys.path.insert(0, str(EQUATORIAL_DIR / "scripts"))
import render_equator_belt_road_surface_status_map as source_map  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export source data for the thesis equator belt map.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    countries = source_map.load_country_configs()
    missing = {iso for iso in countries if not source_map.has_road_surface(iso)}
    world = gpd.read_file(source_map.NATURAL_EARTH).to_crs("EPSG:4326")
    world_clip = gpd.clip(world, box(-180, -28, 180, 28))

    selected_rows = []
    for iso in countries:
        rows = source_map.country_geometry(world, iso)
        if rows.empty:
            continue
        row = rows.iloc[0].copy()
        row["country_code"] = iso
        row["label"] = countries[iso]
        row["missing_road_surface"] = iso in missing
        row["no_crop_candidates"] = iso in source_map.NO_CROP_CANDIDATES
        label_x, label_y = source_map.label_point(row, iso)
        row["label_x"] = label_x
        row["label_y"] = label_y
        selected_rows.append(row)
    selected = gpd.GeoDataFrame(selected_rows, geometry="geometry", crs=world.crs)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        args.out.unlink()
    world_clip.to_file(args.out, layer="world_clip", driver="GPKG")
    selected.to_file(args.out, layer="selected_countries", driver="GPKG")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_generator": str(source_map.Path(source_map.__file__).resolve()),
        "geopackage": str(args.out),
        "countries": len(countries),
        "missing_road_surface": sorted(missing),
        "no_crop_candidates": sorted(source_map.NO_CROP_CANDIDATES),
        "layers": {
            "world_clip": len(world_clip),
            "selected_countries": len(selected),
        },
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
