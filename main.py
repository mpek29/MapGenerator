from map_generator import (
    load_data,
    detect_columns,
    add_paris_if_needed,
    merge_data,
    compute_density,
    plot_density_map,
    plot_threshold_map,
    export_map_filename
)

if __name__ == "__main__":
    communes_path = 'communes.json'
    pop_path = 'POPULATION_MUNICIPALE_COMMUNES_FRANCE.xlsx'
    gdf, pop = load_data(communes_path, pop_path)
    insee_gdf_col, insee_pop_col, pop_col = detect_columns(gdf, pop)
    pop = add_paris_if_needed(pop, insee_pop_col, pop_col)
    gdf = merge_data(gdf, pop, insee_gdf_col, insee_pop_col)
    gdf = compute_density(gdf, pop_col)

    # First chart: full density map
    output_path1 = export_map_filename(prefix='france_density_map')
    plot_density_map(gdf, output_path=output_path1, show=False)
    print(f"Map exported to {output_path1}")

    # Second chart: thresholded map
    output_path2 = export_map_filename(prefix='france_density_threshold_map')
    plot_threshold_map(gdf, output_path=output_path2, show=False, threshold=1500.0)
    print(f"Thresholded map exported to {output_path2}")
