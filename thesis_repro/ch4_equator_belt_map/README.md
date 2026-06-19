# Chapter 4 Equator Belt Map Reproduction

This folder keeps the thesis-specific source render and data for the equator belt map.

- Source generator found in the main repo: `equatorial/scripts/render_equator_belt_road_surface_status_map.py`.
- `scripts/render_equator_belt_road_surface_status_map.py` is a copy of that source generator.
- `scripts/export_equator_belt_map_data.py` exports the selected map layers to `data/equator_belt_map_data.gpkg`.
- `scripts/render_equator_belt_from_data.py` renders from the saved GeoPackage, without needing the equatorial YAML/config folders.
- `data/equator_belt_map_source_manifest.json` records the source-render command and axis/canvas parameters.
- `outputs/equator_belt_map_source_xcropped_taller.png` is copied to `../../images/ch4/equator_belt_map_source_xcropped_taller.png`.

Run from repository root:

```bash
equatorial/.venv/bin/python itmo-phd-thesis-template-en/thesis_repro/ch4_equator_belt_map/scripts/export_equator_belt_map_data.py
equatorial/.venv/bin/python itmo-phd-thesis-template-en/thesis_repro/ch4_equator_belt_map/scripts/render_equator_belt_from_data.py
```

Default thesis render:

- x-axis bounds: `[-120, 164]`, cropping the left side further by longitude.
- figure size: `20 x 6.3` inches at `180 dpi`.
- axis aspect: `auto`, which vertically stretches the map instead of only adding blank canvas.
