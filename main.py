from pathlib import Path

import geopandas as gpd
import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series
from pandera.typing.geopandas import GeoDataFrame, GeoSeries


class Lights(pa.DataFrameModel):
    light_id: Series[str] = pa.Field(unique=True)
    geometry: GeoSeries

    @pa.dataframe_check
    def points_only(self, gdf: GeoDataFrame) -> pd.Series:
        return gdf.geometry.geom_type == "Point"

    class Config(pa.DataFrameModel.Config):
        strict = "filter"
        coerce = False

def load_lights(path: Path):
    gdf = gpd.read_file(path)

    if "light_id" not in gdf.columns:
        raise ValueError(f"{path} has no light_id property on its features")

    gdf = gdf.dropna(subset=["light_id"]) # filter null id
    return Lights.validate(gdf, lazy=True)

class Roads(pa.DataFrameModel):
    id: str
    geometry: GeoSeries

    def __init__(self, path):
        self.roads = gpd.read_file(path)
        # validate the geometry is LineString

    def find_closest_roads(self, lights: Lights):
        # use the dist_fast alg
        return None


def main():
    load_lights(Path("lights.geojson"))
    print("Hello from ironbark!")


if __name__ == "__main__":
    main()
