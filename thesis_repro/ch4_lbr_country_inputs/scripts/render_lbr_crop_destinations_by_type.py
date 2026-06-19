#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
THESIS_DIR = PACKAGE_DIR.parents[1]
DEFAULT_DATA = PACKAGE_DIR / "data/lbr_country_inputs.gpkg"
DEFAULT_OUT = PACKAGE_DIR / "outputs/lbr_crop_destinations_by_type.png"
DEFAULT_THESIS_IMAGE = THESIS_DIR / "images/ch4/lbr_crop_destinations_by_type.png"


def read_layer(path: Path, layer: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path, layer=layer).to_crs("EPSG:4326")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the LBR destination-type row for thesis Figure 4.2.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--thesis-image", type=Path, default=DEFAULT_THESIS_IMAGE)
    parser.add_argument("--no-copy-to-thesis", action="store_true")
    args = parser.parse_args()

    boundary = read_layer(args.data, "boundary")
    roads = read_layer(args.data, "road_edges")
    city_5_100 = read_layer(args.data, "cities_5_100k")
    city_100 = read_layer(args.data, "cities_100k_plus")
    ports = read_layer(args.data, "ports")
    airports = read_layer(args.data, "airports")

    geom = boundary.geometry.iloc[0]
    minx, miny, maxx, maxy = geom.bounds
    pad_x = max((maxx - minx) * 0.05, 0.1)
    pad_y = max((maxy - miny) * 0.05, 0.1)

    fig, axes = plt.subplots(1, 5, figsize=(18, 4.8), constrained_layout=True)
    road_colors = {"paved": "#377dde", "unpaved": "#d2692c", "unknown": "#b8b8b8"}
    panel_titles = ["roads", "cities 5-100k", "cities 100k+", "ports", "airports"]
    legend_handles = {
        "roads": [
            Line2D([0], [0], color=road_colors["paved"], linewidth=1.4, label="paved"),
            Line2D([0], [0], color=road_colors["unpaved"], linewidth=1.4, label="unpaved"),
            Line2D([0], [0], color=road_colors["unknown"], linewidth=1.4, label="unknown"),
        ],
        "cities 5-100k": [
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#6f4bc4", markeredgecolor="#2b145e", markersize=6, label="cities 5-100k"),
        ],
        "cities 100k+": [
            Line2D([0], [0], marker="s", color="none", markerfacecolor="#f39c34", markeredgecolor="#8a4a00", markersize=6, label="cities 100k+"),
        ],
        "ports": [
            Line2D([0], [0], marker="P", color="none", markerfacecolor="#0c6b79", markeredgecolor="#083d45", markersize=6, label="ports"),
        ],
        "airports": [
            Line2D([0], [0], marker="^", color="none", markerfacecolor="#2ca25f", markeredgecolor="#145a32", markersize=6, label="airports"),
        ],
    }

    for ax, title in zip(axes, panel_titles, strict=True):
        boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.7, zorder=2)
        if title == "roads":
            surface = roads["surface_group"].fillna("unknown")
            for group, lw, alpha in [("unknown", 0.22, 0.55), ("unpaved", 0.30, 0.85), ("paved", 0.55, 0.9)]:
                sub = roads[surface.eq(group)]
                if not sub.empty:
                    sub.plot(ax=ax, color=road_colors[group], linewidth=lw, alpha=alpha, zorder=1)

        if title == "cities 5-100k" and not city_5_100.empty:
            sizes = np.clip(np.sqrt(city_5_100["population"].fillna(5000).to_numpy(float)) / 3.0, 18, 90)
            ax.scatter(city_5_100.geometry.x, city_5_100.geometry.y, s=sizes, c="#6f4bc4", edgecolors="#2b145e", linewidths=0.35, alpha=0.9, zorder=6)
        elif title == "cities 100k+" and not city_100.empty:
            sizes = np.clip(np.sqrt(city_100["population"].fillna(100000).to_numpy(float)) / 9.0, 45, 120)
            ax.scatter(city_100.geometry.x, city_100.geometry.y, s=sizes, c="#f39c34", marker="s", edgecolors="#8a4a00", linewidths=0.45, alpha=0.9, zorder=6)
        elif title == "ports" and not ports.empty:
            ax.scatter(ports.geometry.x, ports.geometry.y, s=75, c="#0c6b79", marker="P", edgecolors="#083d45", linewidths=0.45, alpha=0.95, zorder=6)
        elif title == "airports" and not airports.empty:
            ax.scatter(airports.geometry.x, airports.geometry.y, s=42, c="#2ca25f", marker="^", edgecolors="#145a32", linewidths=0.45, alpha=0.95, zorder=6)

        ax.set_title(title)
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.legend(
            handles=legend_handles[title],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.03),
            ncol=len(legend_handles[title]),
            frameon=False,
            fontsize=8,
            handlelength=1.5,
            columnspacing=0.8,
        )

    fig.suptitle("LBR roads and destination nodes by type")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    plt.close(fig)

    if not args.no_copy_to_thesis:
        args.thesis_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.out, args.thesis_image)

    print(f"wrote={args.out}")
    if not args.no_copy_to_thesis:
        print(f"copied={args.thesis_image}")
    print(
        "counts "
        f"roads={len(roads)} cities_5_100k={len(city_5_100)} "
        f"cities_100k={len(city_100)} ports={len(ports)} airports={len(airports)}"
    )


if __name__ == "__main__":
    main()
