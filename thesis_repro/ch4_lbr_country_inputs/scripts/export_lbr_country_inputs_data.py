#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import psycopg
import xarray as xr
from shapely import contains_xy


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
REPO_DIR = PACKAGE_DIR.parents[2]
DEFAULT_DB_URL = "postgresql://gk@127.0.0.1:5432/equatorial"
DEFAULT_GADM = REPO_DIR / "equatorial/data/raw/gadm/LBR/gadm41_LBR.gpkg"
DEFAULT_CROPGRIDS_NC_DIR = REPO_DIR / "equatorial/data/raw/cropgrids/selected_nc"
DEFAULT_OUT = PACKAGE_DIR / "data/lbr_country_inputs.gpkg"
DEFAULT_MANIFEST = PACKAGE_DIR / "data/lbr_country_inputs_manifest.json"
CROP_LAYERS = ["avocado", "banana", "plantain", "mango", "pineapple"]


def read_sql(conn: psycopg.Connection, sql: str, params: tuple = ()) -> gpd.GeoDataFrame:
    frame = gpd.read_postgis(sql, conn, geom_col="geometry", params=params)
    return frame.set_crs("EPSG:4326", allow_override=True)


def lon_lat_names(dataset: xr.Dataset) -> tuple[str, str]:
    lon_name = next((name for name in ["lon", "longitude", "x"] if name in dataset.coords), None)
    lat_name = next((name for name in ["lat", "latitude", "y"] if name in dataset.coords), None)
    if lon_name is None or lat_name is None:
        raise ValueError(f"Cannot identify lon/lat coordinates: {list(dataset.coords)}")
    return lon_name, lat_name


def export_crop_preview_cells(nc_dir: Path, country_geom) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = country_geom.bounds
    frames = []
    for crop in CROP_LAYERS:
        path = nc_dir / f"CROPGRIDSv1.08_{crop}.nc"
        if not path.exists():
            raise FileNotFoundError(path)
        with xr.open_dataset(path) as dataset:
            data = dataset["harvarea"]
            lon_name, lat_name = lon_lat_names(dataset)
            lons = np.asarray(dataset[lon_name].values, dtype="float64")
            lats = np.asarray(dataset[lat_name].values, dtype="float64")
            lon_mask = (lons >= minx - 0.05) & (lons <= maxx + 0.05)
            lat_mask = (lats >= miny - 0.05) & (lats <= maxy + 0.05)
            subset = data.isel({lon_name: np.where(lon_mask)[0], lat_name: np.where(lat_mask)[0]})
            values = np.asarray(subset.values, dtype="float64")
            sub_lons = np.asarray(subset[lon_name].values, dtype="float64")
            sub_lats = np.asarray(subset[lat_name].values, dtype="float64")
            if data.dims.index(lat_name) > data.dims.index(lon_name):
                values = values.T
            lon_grid, lat_grid = np.meshgrid(sub_lons, sub_lats)
            valid = np.isfinite(values) & (values > 0)
            valid &= contains_xy(country_geom, lon_grid, lat_grid)
            if not valid.any():
                continue
            flat_values = values[valid]
            flat_lons = lon_grid[valid]
            flat_lats = lat_grid[valid]
            order = np.argsort(flat_values)[::-1]
            keep = order[: min(5000, len(order))]
            frame = gpd.GeoDataFrame(
                {
                    "country_code": "LBR",
                    "crop_code": crop,
                    "harvested_area": flat_values[keep],
                    "lon": flat_lons[keep],
                    "lat": flat_lats[keep],
                },
                geometry=gpd.points_from_xy(flat_lons[keep], flat_lats[keep]),
                crs="EPSG:4326",
            )
            frames.append(frame)
    if not frames:
        return gpd.GeoDataFrame(columns=["country_code", "crop_code", "harvested_area", "lon", "lat", "geometry"], geometry="geometry", crs="EPSG:4326")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:4326")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LBR thesis input-map layers from the equatorial PostGIS DB.")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    parser.add_argument("--gadm", type=Path, default=DEFAULT_GADM)
    parser.add_argument("--cropgrids-nc-dir", type=Path, default=DEFAULT_CROPGRIDS_NC_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    boundary = gpd.read_file(args.gadm, layer="ADM_ADM_0").to_crs("EPSG:4326")
    country_geom = boundary.geometry.iloc[0]
    minx, miny, maxx, maxy = country_geom.bounds

    with psycopg.connect(args.db_url) as conn:
        layers: dict[str, gpd.GeoDataFrame] = {
            "boundary": boundary[["GID_0", "COUNTRY", "geometry"]].copy(),
            "road_edges": read_sql(
                conn,
                """
                SELECT edge_id, country_code, surface_group, highway, length_km, base_time_h, geometry
                FROM eq.road_graph_edges_lbr
                WHERE geometry IS NOT NULL
                """,
            ),
            "crop_origin_nodes": read_sql(
                conn,
                """
                SELECT country_code, crop_code, candidate_rank, harvested_area, cluster_cell_count,
                       lon, lat, node_id, node_distance_m, geometry
                FROM eq.crop_origin_nodes_lbr
                WHERE country_code = 'LBR'
                ORDER BY crop_code, candidate_rank
                """,
            ),
            "crop_cluster_nodes": read_sql(
                conn,
                """
                SELECT o.country_code, o.crop_code, o.candidate_rank, o.harvested_area,
                       o.cluster_cell_count, o.lon AS representative_lon, o.lat AS representative_lat,
                       o.node_id, o.node_distance_m,
                       ST_X(n.geometry) AS node_lon, ST_Y(n.geometry) AS node_lat,
                       o.geometry
                FROM eq.crop_origin_nodes_lbr o
                LEFT JOIN eq.road_graph_nodes_lbr n ON n.node_id = o.node_id
                WHERE o.country_code = 'LBR'
                ORDER BY o.crop_code, o.candidate_rank
                """,
            ),
            "cities_5_100k": read_sql(
                conn,
                """
                SELECT country_code, geoname_id, name, population, lon, lat, geometry
                FROM eq.city_destinations_5k_100k
                WHERE country_code = 'LBR'
                ORDER BY population DESC NULLS LAST
                """,
            ),
            "cities_100k_plus": read_sql(
                conn,
                """
                SELECT country_code, geoname_id, name, population, lon, lat, geometry
                FROM eq.city_destinations
                WHERE country_code = 'LBR' AND population >= 100000
                ORDER BY population DESC NULLS LAST
                """,
            ),
            "ports": read_sql(
                conn,
                """
                SELECT port_id, name, natlscale, lon, lat, geometry
                FROM eq.port_destinations
                WHERE lon BETWEEN %s AND %s AND lat BETWEEN %s AND %s
                ORDER BY natlscale DESC NULLS LAST, name NULLS LAST
                """,
                (minx - 0.1, maxx + 0.1, miny - 0.1, maxy + 0.1),
            ),
            "airports": read_sql(
                conn,
                """
                SELECT airport_id, ident, airport_type, name, iso_country, municipality,
                       scheduled_service, iata_code, lon, lat, geometry
                FROM eq.airport_destinations
                WHERE iso_country = 'LR'
                  AND airport_type IN ('large_airport', 'medium_airport', 'small_airport')
                ORDER BY airport_type, name
                """,
            ),
        }

    layers["crop_preview_cells"] = export_crop_preview_cells(args.cropgrids_nc_dir, country_geom)

    for name in ("ports", "airports"):
        frame = layers[name]
        if not frame.empty:
            inside = contains_xy(country_geom, frame.geometry.x.to_numpy(float), frame.geometry.y.to_numpy(float))
            layers[name] = frame.loc[inside].copy()

    if args.out.exists():
        args.out.unlink()
    for layer_name, frame in layers.items():
        frame.to_file(args.out, layer=layer_name, driver="GPKG")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "db_url": args.db_url,
        "gadm": str(args.gadm),
        "geopackage": str(args.out),
        "layers": {name: {"rows": int(len(frame)), "columns": list(frame.columns)} for name, frame in layers.items()},
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"geopackage": str(args.out), "manifest": str(args.manifest), "rows": {k: len(v) for k, v in layers.items()}}, indent=2))


if __name__ == "__main__":
    main()
