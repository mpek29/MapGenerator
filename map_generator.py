"""
map_generator.py
Professional map generation module for French municipality population density.
"""
import os
import datetime
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


def load_data(communes_path: str, pop_path: str):
    """Load and return GeoDataFrame and population DataFrame."""
    if not os.path.exists(communes_path) or not os.path.exists(pop_path):
        raise FileNotFoundError("Missing data files. Please ensure both files are in the project root.")
    gdf = gpd.read_file(communes_path)
    pop = pd.read_excel(pop_path)
    return gdf, pop


def detect_columns(gdf: pd.DataFrame, pop: pd.DataFrame):
    """Detect INSEE and population columns."""
    possible_insee_gdf = [col for col in gdf.columns if 'INSEE' in col.upper() or 'COD' in col.upper()]
    possible_insee_pop = [col for col in pop.columns if 'INSEE' in col.upper() or 'COD' in col.upper()]
    insee_gdf_col = possible_insee_gdf[0] if possible_insee_gdf else gdf.columns[0]
    insee_pop_col = possible_insee_pop[0] if possible_insee_pop else pop.columns[0]
    pop_col = 'p21_pop' if 'p21_pop' in pop.columns else pop.columns[-1]
    return insee_gdf_col, insee_pop_col, pop_col


def add_paris_if_needed(pop: pd.DataFrame, insee_col: str, pop_col: str) -> pd.DataFrame:
    """If Paris (75056) is missing but arrondissements are present, add Paris as sum of arrondissements."""
    paris_code = '75056'
    arrdt_codes = [f'75{str(i).zfill(3)}' for i in range(101, 121)]
    if (paris_code not in pop[insee_col].astype(str).values) and any(code in pop[insee_col].astype(str).values for code in arrdt_codes):
        arrdt_mask = pop[insee_col].astype(str).isin(arrdt_codes)
        arrdt_rows = pop[arrdt_mask]
        summed = arrdt_rows.select_dtypes(include='number').sum(numeric_only=True)
        first_row = arrdt_rows.iloc[0].copy()
        first_row[insee_col] = paris_code
        first_row['libgeo'] = 'Paris'
        for col in arrdt_rows.select_dtypes(include='number').columns:
            first_row[col] = summed[col]
        pop = pd.concat([pop, pd.DataFrame([first_row])], ignore_index=True)
    return pop


def merge_data(gdf: gpd.GeoDataFrame, pop: pd.DataFrame, insee_gdf_col: str, insee_pop_col: str) -> gpd.GeoDataFrame:
    """Merge GeoDataFrame and population DataFrame on INSEE code."""
    return gdf.merge(pop, left_on=insee_gdf_col, right_on=insee_pop_col)


def compute_density(gdf: gpd.GeoDataFrame, pop_col: str) -> gpd.GeoDataFrame:
    """Compute area and density, and classify into 5 bins."""
    gdf['area_km2'] = gdf['geometry'].area / 1e6
    gdf['density'] = gdf[pop_col] / gdf['area_km2']
    bins = [0, 15, 30, 50, 100, np.inf]
    labels = ['0-15', '15-30', '30-50', '50-100', '100+']
    gdf['density_class'] = pd.cut(gdf['density'], bins=bins, labels=labels, include_lowest=True, right=False)
    return gdf



def plot_density_map(gdf: gpd.GeoDataFrame, output_path: str = None, show: bool = True):
    """Plot and optionally export the density map as PNG."""
    red_palette = ListedColormap(['#fff5f0', '#fcbba1', '#fc9272', '#de2d26', '#a50f15'])
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    gdf.plot(
        column='density_class',
        ax=ax,
        legend=True,
        cmap=red_palette,
        linewidth=0.1,
        edgecolor='grey',
        categorical=True
    )
    plt.title('Population Density by Municipality in France (2021)\n(hab/km², 5 niveaux de rouge)')
    plt.axis('off')
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    plt.close(fig)


def plot_threshold_map(gdf: gpd.GeoDataFrame, output_path: str = None, show: bool = True, threshold: float = 100.0):
    """Plot a thresholded map: only municipalities with density >= threshold in red (#DE2D26), others fully transparent."""
    import matplotlib.colors as mcolors
    # Filter for density >= threshold
    mask = gdf['density'] >= threshold
    gdf_red = gdf[mask]
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    # Plot only the red municipalities
    if not gdf_red.empty:
        gdf_red.plot(
            ax=ax,
            color='#de2d26',
            linewidth=0,
            edgecolor='none'
        )
    # Remove axis and background
    ax.set_facecolor('none')
    plt.title(f'Thresholded Population Density (>= {threshold} hab/km² in red)')
    plt.axis('off')
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=True)
    if show:
        plt.show()
    plt.close(fig)


def export_map_filename(prefix: str = 'france_density_map') -> str:
    """Generate a timestamped filename for map export."""
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{now}.png"



def main(communes_path: str, pop_path: str, export: bool = True):
    """Main workflow for generating and exporting both maps."""
    gdf, pop = load_data(communes_path, pop_path)
    insee_gdf_col, insee_pop_col, pop_col = detect_columns(gdf, pop)
    pop = add_paris_if_needed(pop, insee_pop_col, pop_col)
    gdf = merge_data(gdf, pop, insee_gdf_col, insee_pop_col)
    gdf = compute_density(gdf, pop_col)
    output_path1 = None
    output_path2 = None
    if export:
        output_path1 = export_map_filename(prefix='france_density_map')
        output_path2 = export_map_filename(prefix='france_density_threshold_map')
    # First chart: full density map
    plot_density_map(gdf, output_path=output_path1, show=True)
    if export:
        print(f"Map exported to {output_path1}")
    # Second chart: thresholded map
    plot_threshold_map(gdf, output_path=output_path2, show=True, threshold=100.0)
    if export:
        print(f"Thresholded map exported to {output_path2}")

if __name__ == "__main__":
    main('communes.json', 'POPULATION_MUNICIPALE_COMMUNES_FRANCE.xlsx')
