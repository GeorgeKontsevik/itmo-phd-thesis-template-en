#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
THESIS_DIR = PACKAGE_DIR.parents[1]
DEFAULT_DATA = PACKAGE_DIR / "data/equator_belt_map_data.gpkg"
DEFAULT_OUT = PACKAGE_DIR / "outputs/equator_belt_map_source_xcropped_taller.png"
DEFAULT_THESIS_IMAGE = THESIS_DIR / "images/ch4/equator_belt_map_source_xcropped_taller.png"
BELT_KM = 700
BELT_DEG = BELT_KM / 111.32
COUNTRY_LABELS_RU = {
    "Angola": "Ангола",
    "Benin": "Бенин",
    "Brazil": "Бразилия",
    "Brunei": "Бруней",
    "Burundi": "Бурунди",
    "Cameroon": "Камерун",
    "Central African\nRepublic": "ЦАР",
    "Coast": "Кот-д'Ивуар",
    "Colombia": "Колумбия",
    "Congo": "Конго",
    "DR Congo": "ДР Конго",
    "Ecuador": "Эквадор",
    "Eq. Guinea": "Экв. Гвинея",
    "Ethiopia": "Эфиопия",
    "France\n(French Guiana)": "Франция\n(Гвиана)",
    "Gabon": "Габон",
    "Ghana": "Гана",
    "Guayana": "Гайана",
    "Indonesia": "Индонезия",
    "Kenya": "Кения",
    "Liberia": "Либерия",
    "Malaysia": "Малайзия",
    "Nigeria": "Нигерия",
    "Papua New\nGuinea": "Папуа-\nНовая Гвинея",
    "Peru": "Перу",
    "Philippines": "Филиппины",
    "Rwanda": "Руанда",
    "Somalia": "Сомали",
    "South Sudan": "Южный Судан",
    "Sri Lanka": "Шри-Ланка",
    "Suriname": "Суринам",
    "Tanzania": "Танзания",
    "Thailand": "Таиланд",
    "Togo": "Того",
    "Uganda": "Уганда",
    "Venezuela": "Венесуэла",
}


def country_label_ru(value: str) -> str:
    return COUNTRY_LABELS_RU.get(value, value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render thesis equator belt map from saved GeoPackage layers.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--thesis-image", type=Path, default=DEFAULT_THESIS_IMAGE)
    parser.add_argument("--xmin", type=float, default=-120.0)
    parser.add_argument("--xmax", type=float, default=164.0)
    parser.add_argument("--ymin", type=float, default=-28.0)
    parser.add_argument("--ymax", type=float, default=28.0)
    parser.add_argument("--fig-width", type=float, default=20.0)
    parser.add_argument("--fig-height", type=float, default=6.3)
    parser.add_argument("--aspect", default="auto", choices=["auto", "equal"], help="Axis aspect; auto vertically stretches the map.")
    parser.add_argument("--no-copy-to-thesis", action="store_true")
    args = parser.parse_args()

    world_clip = gpd.read_file(args.data, layer="world_clip").to_crs("EPSG:4326")
    selected = gpd.read_file(args.data, layer="selected_countries").to_crs("EPSG:4326")

    fig, ax = plt.subplots(figsize=(args.fig_width, args.fig_height))
    world_clip.plot(ax=ax, color="#f7f7f4", edgecolor="#dadada", linewidth=0.55, zorder=1)
    regular = ~(selected["missing_road_surface"] | selected["no_crop_candidates"])
    selected.loc[regular].plot(ax=ax, color="#f2d59a", edgecolor="#9c650f", linewidth=0.9, zorder=3)
    selected.loc[selected["missing_road_surface"]].plot(
        ax=ax, color="#f2d59a", edgecolor="#8f1d1d", linewidth=1.25, hatch="////", zorder=4
    )
    selected.loc[selected["no_crop_candidates"]].plot(
        ax=ax, color="#f2d59a", edgecolor="#2f5597", linewidth=1.25, hatch="\\\\\\\\", zorder=4
    )

    ax.axhline(0, color="#e31a1c", linewidth=2.2, label="Экватор", zorder=5)
    ax.axhline(BELT_DEG, color="#1f70c1", linewidth=1.8, linestyle="--", label="+700 км от экватора", zorder=5)
    ax.axhline(-BELT_DEG, color="#1f70c1", linewidth=1.8, linestyle="--", label="-700 км от экватора", zorder=5)

    for row in selected.itertuples(index=False):
        ax.text(
            row.label_x,
            row.label_y,
            country_label_ru(row.label),
            ha="center",
            va="center",
            fontsize=7.5,
            color="#333333",
            bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "#777777", "alpha": 0.86},
            clip_on=False,
            zorder=6,
        )

    loaded_patch = mpatches.Patch(facecolor="#f2d59a", edgecolor="#9c650f", label="Есть слой типов дорог")
    missing_patch = mpatches.Patch(facecolor="#f2d59a", edgecolor="#8f1d1d", hatch="////", label="Нет слоя типов дорог")
    no_crop_patch = mpatches.Patch(facecolor="#f2d59a", edgecolor="#2f5597", hatch="\\\\\\\\", label="Нет кандидатов культур")
    handles, _ = ax.get_legend_handles_labels()
    handles.extend([loaded_patch, missing_patch, no_crop_patch])
    ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=10)

    ax.set_xlim(args.xmin, args.xmax)
    ax.set_ylim(args.ymin, args.ymax)
    ax.set_aspect(args.aspect)
    ax.set_xlabel("Долгота")
    ax.set_ylabel("Широта")
    ax.set_title("Страны в поясе 700 км от экватора:\nпокрытие дорог и наличие данных по культурам")
    ax.grid(alpha=0.18)
    fig.tight_layout()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    plt.close(fig)
    print(f"wrote={args.out}")

    if not args.no_copy_to_thesis:
        args.thesis_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.out, args.thesis_image)
        print(f"copied={args.thesis_image}")


if __name__ == "__main__":
    main()
