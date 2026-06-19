# Chapter 4 LBR Country Inputs Reproduction

This folder keeps the thesis-specific scripts and data needed to reproduce the LBR input-map row with five maps:

- `data/lbr_country_inputs.gpkg` contains the exported spatial layers.
- `data/lbr_country_inputs_manifest.json` records row counts and source tables.
- `scripts/export_lbr_country_inputs_data.py` rebuilds the GeoPackage from the local equatorial PostGIS database.
- `scripts/render_lbr_crop_destinations_by_type.py` renders `outputs/lbr_crop_destinations_by_type.png` and copies it to `../../images/ch4/lbr_crop_destinations_by_type.png` by default.
- `scripts/render_lbr_crop_rows.py` renders `outputs/lbr_crop_distribution.png` and `outputs/lbr_crop_clusters_nodes.png`, then copies them to `../../images/ch4/` by default.

The rendered row shows roads and destination nodes by type only. Crop clusters are kept in the exported data for traceability, but they are not drawn in this figure version. Each map panel has its own legend below the panel.
The crop distribution row and the crop clusters / road nodes row also include a legend below each individual map panel.

Run from repository root:

```bash
equatorial/.venv/bin/python itmo-phd-thesis-template-en/thesis_repro/ch4_lbr_country_inputs/scripts/export_lbr_country_inputs_data.py
equatorial/.venv/bin/python itmo-phd-thesis-template-en/thesis_repro/ch4_lbr_country_inputs/scripts/render_lbr_crop_destinations_by_type.py
equatorial/.venv/bin/python itmo-phd-thesis-template-en/thesis_repro/ch4_lbr_country_inputs/scripts/render_lbr_crop_rows.py
```

Expected exported layer counts at creation time:

- `boundary`: 1
- `road_edges`: 45,704
- `crop_origin_nodes`: 97
- `crop_cluster_nodes`: 97
- `crop_preview_cells`: 4,868
- `cities_5_100k`: 21
- `cities_100k_plus`: 1
- `ports`: 1
- `airports`: 19
