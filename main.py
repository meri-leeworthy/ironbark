from pathlib import Path
from typing import cast

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

    duplicates = gdf[gdf.duplicated(subset="light_id", keep="first")]
    if not duplicates.empty:
        print(f"Warning: dropping {len(duplicates)} features with duplicate ids")

    gdf = gdf.drop_duplicates(subset="light_id", keep="first")

    return cast(GeoDataFrame[Lights], Lights.validate(gdf, lazy=True))

class Roads(pa.DataFrameModel):
    road_id: Series[str] = pa.Field(unique=True)
    geometry: GeoSeries

    @pa.dataframe_check
    def linestring_only(self, gdf: GeoDataFrame) -> pd.Series:
        return gdf.geometry.geom_type == "LineString"

    def find_closest_roads(self, lights: Lights):
        # use the dist_fast alg
        return None

def load_roads(path: Path):
    gdf = gpd.read_file(path)
    return cast(GeoDataFrame[Roads], Roads.validate(gdf, lazy=True))


def main():
    lights = load_lights(Path("lights.geojson"))
    roads = load_roads(Path("roads.geojson"))
    print(roads)


if __name__ == "__main__":
    main()
