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
DEFAULT_OUT_DIR = PACKAGE_DIR / "outputs"
DEFAULT_THESIS_IMAGE_DIR = THESIS_DIR / "images/ch4"
CROP_LAYERS = ["avocado", "banana", "plantain", "mango", "pineapple"]
CROP_LABELS = {
    "avocado": "авокадо",
    "banana": "банан",
    "plantain": "плантан",
    "mango": "манго",
    "pineapple": "ананас",
}


def read_layer(path: Path, layer: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path, layer=layer).to_crs("EPSG:4326")


def set_country_extent(ax, boundary: gpd.GeoDataFrame) -> None:
    minx, miny, maxx, maxy = boundary.geometry.iloc[0].bounds
    pad_x = max((maxx - minx) * 0.05, 0.1)
    pad_y = max((maxy - miny) * 0.05, 0.1)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_xticks([])
    ax.set_yticks([])


def crop_label(crop: str) -> str:
    return CROP_LABELS.get(crop, crop)


def render_distribution(boundary: gpd.GeoDataFrame, preview: gpd.GeoDataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, len(CROP_LAYERS), figsize=(18, 4.9), constrained_layout=True)
    for ax, crop in zip(axes, CROP_LAYERS, strict=True):
        boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.7)
        sub = preview[preview["crop_code"].eq(crop)]
        scatter = None
        if not sub.empty:
            sizes = np.clip(np.sqrt(sub["harvested_area"].to_numpy(dtype=float)), 4, 45)
            scatter = ax.scatter(
                sub.geometry.x,
                sub.geometry.y,
                c=sub["harvested_area"],
                s=sizes,
                cmap="viridis",
                alpha=0.78,
                linewidths=0,
            )
        ax.set_title(crop_label(crop))
        set_country_extent(ax, boundary)
        if scatter is not None:
            cbar = fig.colorbar(scatter, ax=ax, orientation="horizontal", pad=0.035, fraction=0.055)
            cbar.ax.tick_params(labelsize=6, length=2, pad=1)
            cbar.set_label("убранная площадь", fontsize=7, labelpad=1)

    fig.suptitle("Либерия, CROPGRIDS 2020: распределение убранной площади по культурам")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_clusters_nodes(boundary: gpd.GeoDataFrame, preview: gpd.GeoDataFrame, clusters: gpd.GeoDataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, len(CROP_LAYERS), figsize=(18, 4.9), constrained_layout=True)
    legend_handles = [
        Line2D([0], [0], marker=".", color="none", markerfacecolor="#7a7a7a", markeredgecolor="#7a7a7a", alpha=0.35, markersize=7, label="ячейки культуры"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none", markeredgecolor="#d7191c", markersize=6, label="кластерная ячейка"),
        Line2D([0], [0], marker="x", color="#2c7bb6", linestyle="none", markersize=5, label="дорожный узел"),
        Line2D([0], [0], color="#111111", linewidth=0.5, alpha=0.55, label="привязка к узлу"),
    ]
    for ax, crop in zip(axes, CROP_LAYERS, strict=True):
        boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.7)
        raw_sub = preview[preview["crop_code"].eq(crop)]
        if not raw_sub.empty:
            sizes = np.clip(np.sqrt(raw_sub["harvested_area"].to_numpy(dtype=float)), 2, 18)
            ax.scatter(raw_sub.geometry.x, raw_sub.geometry.y, c="#7a7a7a", s=sizes, alpha=0.22, linewidths=0)

        cluster_sub = clusters[clusters["crop_code"].eq(crop)]
        if not cluster_sub.empty:
            for row in cluster_sub.itertuples(index=False):
                if np.isfinite(row.node_lon) and np.isfinite(row.node_lat):
                    ax.plot(
                        [row.representative_lon, row.node_lon],
                        [row.representative_lat, row.node_lat],
                        color="#111111",
                        linewidth=0.35,
                        alpha=0.5,
                    )
            cluster_sizes = np.clip(np.sqrt(cluster_sub["harvested_area"].to_numpy(dtype=float)), 35, 170)
            ax.scatter(
                cluster_sub["representative_lon"],
                cluster_sub["representative_lat"],
                s=cluster_sizes,
                facecolors="none",
                edgecolors="#d7191c",
                linewidths=1.4,
            )
            node_sub = cluster_sub.dropna(subset=["node_lon", "node_lat"])
            if not node_sub.empty:
                ax.scatter(node_sub["node_lon"], node_sub["node_lat"], s=22, c="#2c7bb6", marker="x", linewidths=1.0)

        ax.set_title(crop_label(crop))
        set_country_extent(ax, boundary)
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.03),
            ncol=2,
            frameon=False,
            fontsize=6.5,
            handlelength=1.3,
            columnspacing=0.55,
        )

    fig.suptitle("Либерия, CROPGRIDS: кластеры культур и привязанные дорожные узлы")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render LBR crop distribution and cluster/node rows for thesis Figure 4.2.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--thesis-image-dir", type=Path, default=DEFAULT_THESIS_IMAGE_DIR)
    parser.add_argument("--no-copy-to-thesis", action="store_true")
    args = parser.parse_args()

    boundary = read_layer(args.data, "boundary")
    preview = read_layer(args.data, "crop_preview_cells")
    clusters = read_layer(args.data, "crop_cluster_nodes")

    outputs = {
        "lbr_crop_distribution.png": args.out_dir / "lbr_crop_distribution.png",
        "lbr_crop_clusters_nodes.png": args.out_dir / "lbr_crop_clusters_nodes.png",
    }
    render_distribution(boundary, preview, outputs["lbr_crop_distribution.png"])
    render_clusters_nodes(boundary, preview, clusters, outputs["lbr_crop_clusters_nodes.png"])

    if not args.no_copy_to_thesis:
        args.thesis_image_dir.mkdir(parents=True, exist_ok=True)
        for name, path in outputs.items():
            shutil.copy2(path, args.thesis_image_dir / name)

    print(f"wrote_distribution={outputs['lbr_crop_distribution.png']}")
    print(f"wrote_clusters_nodes={outputs['lbr_crop_clusters_nodes.png']}")
    if not args.no_copy_to_thesis:
        print(f"copied_to={args.thesis_image_dir}")
    print(f"counts preview_cells={len(preview)} clusters={len(clusters)}")


if __name__ == "__main__":
    main()
